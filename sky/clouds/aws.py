"""Amazon Web Services."""
import json
import os
import subprocess
import typing
from typing import Dict, Iterator, List, Optional, Tuple

from sky import clouds
from sky.clouds import service_catalog

if typing.TYPE_CHECKING:
    # renaming to avoid shadowing variables
    from sky import resources as resources_lib

# Minimum set of files under ~/.aws that grant AWS access.
_CREDENTIAL_FILES = [
    'credentials',
]


def _run_output(cmd):
    proc = subprocess.run(cmd,
                          shell=True,
                          check=True,
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE)
    return proc.stdout.decode('ascii')


@clouds.CLOUD_REGISTRY.register
class AWS(clouds.Cloud):
    """Amazon Web Services."""

    _REPR = 'AWS'
    _regions: List[clouds.Region] = []

    #### Regions/Zones ####

    @classmethod
    def regions(cls):
        if not cls._regions:
            # https://aws.amazon.com/premiumsupport/knowledge-center/vpc-find-availability-zone-options/
            cls._regions = [
                clouds.Region('us-west-1').set_zones([
                    clouds.Zone('us-west-1a'),
                    clouds.Zone('us-west-1b'),
                ]),
                clouds.Region('us-west-2').set_zones([
                    clouds.Zone('us-west-2a'),
                    clouds.Zone('us-west-2b'),
                    clouds.Zone('us-west-2c'),
                    clouds.Zone('us-west-2d'),
                ]),
                clouds.Region('us-east-2').set_zones([
                    clouds.Zone('us-east-2a'),
                    clouds.Zone('us-east-2b'),
                    clouds.Zone('us-east-2c'),
                ]),
                clouds.Region('us-east-1').set_zones([
                    clouds.Zone('us-east-1a'),
                    clouds.Zone('us-east-1b'),
                    clouds.Zone('us-east-1c'),
                    clouds.Zone('us-east-1d'),
                    clouds.Zone('us-east-1e'),
                    clouds.Zone('us-east-1f'),
                ]),
            ]
        return cls._regions

    @classmethod
    def region_zones_provision_loop(
        cls,
        *,
        instance_type: Optional[str] = None,
        accelerators: Optional[Dict[str, int]] = None,
        use_spot: bool,
    ) -> Iterator[Tuple[clouds.Region, List[clouds.Zone]]]:
        # AWS provisioner can handle batched requests, so yield all zones under
        # each region.
        del accelerators  # unused

        if instance_type is None:
            # fallback to manually specified region/zones
            regions = cls.regions()
        else:
            regions = service_catalog.get_region_zones_for_instance_type(
                instance_type, use_spot, 'aws')
        for region in regions:
            yield region, region.zones

    @classmethod
    def get_default_ami(cls, region_name: str, instance_type: str) -> str:
        acc = cls.get_accelerators_from_instance_type(instance_type)
        if acc is not None:
            assert len(acc) == 1, acc
            acc_name = list(acc.keys())[0]
            if acc_name == 'K80':
                # Deep Learning AMI GPU PyTorch 1.10.0 (Ubuntu 20.04) 20211208
                # Downgrade the AMI for K80 due as it is only compatible with
                # NVIDIA driver lower than 470.
                amis = {
                    'us-east-1': 'ami-0868a20f5a3bf9702',
                    'us-east-2': 'ami-09b8825010d4dc701',
                    # This AMI is 20210623 as aws does not provide a newer one.
                    'us-west-1': 'ami-0b3c34d643904a734',
                    'us-west-2': 'ami-06b3479ab15aaeaf1',
                }
                assert region_name in amis, region_name
                return amis[region_name]
        # Deep Learning AMI GPU PyTorch 1.10.0 (Ubuntu 20.04) 20220308
        # https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Images:visibility=public-images;v=3;search=:64,:Ubuntu%2020,:Deep%20Learning%20AMI%20GPU%20PyTorch # pylint: disable=line-too-long
        # Nvidia driver: 510.47.03, CUDA Version: 11.6
        amis = {
            'us-east-1': 'ami-0729d913a335efca7',
            'us-east-2': 'ami-070f4af81c19b41bf',
            # This AMI is 20210623 as aws does not provide a newer one.
            'us-west-1': 'ami-0b3c34d643904a734',
            'us-west-2': 'ami-050814f384259894c',
        }
        assert region_name in amis, region_name
        return amis[region_name]

    #### Normal methods ####

    def instance_type_to_hourly_cost(self, instance_type: str, use_spot: bool):
        return service_catalog.get_hourly_cost(instance_type,
                                               region=None,
                                               use_spot=use_spot,
                                               clouds='aws')

    def accelerators_to_hourly_cost(self, accelerators,
                                    use_spot: bool) -> float:
        # AWS includes accelerators as part of the instance type.  Implementing
        # this is also necessary for e.g., the instance may have 4 GPUs, while
        # the task specifies to use 1 GPU.
        return 0

    def get_egress_cost(self, num_gigabytes: float):
        # In general, query this from the cloud:
        #   https://aws.amazon.com/s3/pricing/
        # NOTE: egress from US East (Ohio).
        # NOTE: Not accurate as the pricing tier is based on cumulative monthly
        # usage.
        if num_gigabytes > 150 * 1024:
            return 0.05 * num_gigabytes
        cost = 0.0
        if num_gigabytes >= 50 * 1024:
            cost += (num_gigabytes - 50 * 1024) * 0.07
            num_gigabytes -= 50 * 1024

        if num_gigabytes >= 10 * 1024:
            cost += (num_gigabytes - 10 * 1024) * 0.085
            num_gigabytes -= 10 * 1024

        if num_gigabytes > 1:
            cost += (num_gigabytes - 1) * 0.09

        cost += 0.0
        return cost

    def is_same_cloud(self, other: clouds.Cloud):
        return isinstance(other, AWS)

    @classmethod
    def get_default_instance_type(cls) -> str:
        # 8 vCpus, 32 GB RAM. 3rd generation Intel Xeon. General Purpose.
        return 'm6i.2xlarge'

    # TODO: factor the following three methods, as they are the same logic
    # between Azure and AWS.
    @classmethod
    def get_accelerators_from_instance_type(
        cls,
        instance_type: str,
    ) -> Optional[Dict[str, int]]:
        return service_catalog.get_accelerators_from_instance_type(
            instance_type, clouds='aws')

    def make_deploy_resources_variables(
            self, resources: 'resources_lib.Resources',
            region: Optional['clouds.Region'],
            zones: Optional[List['clouds.Zone']]) -> Dict[str, str]:
        if region is None:
            assert zones is None, (
                'Set either both or neither for: region, zones.')
            region = self._get_default_region()
            zones = region.zones
        else:
            assert zones is not None, (
                'Set either both or neither for: region, zones.')

        region_name = region.name
        zones = [zone.name for zone in zones]

        r = resources
        # r.accelerators is cleared but .instance_type encodes the info.
        acc_dict = self.get_accelerators_from_instance_type(r.instance_type)
        if acc_dict is not None:
            custom_resources = json.dumps(acc_dict, separators=(',', ':'))
        else:
            custom_resources = None

        if r.image_id is not None:
            image_id = r.image_id
        else:
            image_id = self.get_default_ami(region_name, r.instance_type)

        return {
            'instance_type': r.instance_type,
            'custom_resources': custom_resources,
            'use_spot': r.use_spot,
            'region': region_name,
            'zones': ','.join(zones),
            'image_id': image_id,
        }

    def get_feasible_launchable_resources(self,
                                          resources: 'resources_lib.Resources'):
        fuzzy_candidate_list = []
        if resources.instance_type is not None:
            assert resources.is_launchable(), resources
            # Treat Resources(AWS, p3.2x, V100) as Resources(AWS, p3.2x).
            resources = resources.copy(accelerators=None)
            return ([resources], fuzzy_candidate_list)

        def _make(instance_list):
            resource_list = []
            for instance_type in instance_list:
                r = resources.copy(
                    cloud=AWS(),
                    instance_type=instance_type,
                    # Setting this to None as AWS doesn't separately bill /
                    # attach the accelerators.  Billed as part of the VM type.
                    accelerators=None,
                )
                resource_list.append(r)
            return resource_list

        # Currently, handle a filter on accelerators only.
        accelerators = resources.accelerators
        if accelerators is None:
            # No requirements to filter, so just return a default VM type.
            return (_make([AWS.get_default_instance_type()]),
                    fuzzy_candidate_list)

        assert len(accelerators) == 1, resources
        acc, acc_count = list(accelerators.items())[0]
        (instance_list, fuzzy_candidate_list
        ) = service_catalog.get_instance_type_for_accelerator(acc,
                                                              acc_count,
                                                              clouds='aws')
        if instance_list is None:
            return ([], fuzzy_candidate_list)
        return (_make(instance_list), fuzzy_candidate_list)

    def check_credentials(self) -> Tuple[bool, Optional[str]]:
        """Checks if the user has access credentials to this cloud."""
        help_str = (
            ' Run the following commands:'
            '\n      $ pip install boto3'
            '\n      $ aws configure'
            '\n    For more info: '
            'https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html'  # pylint: disable=line-too-long
        )
        # This file is required because it will be synced to remote VMs for
        # `aws` to access private storage buckets.
        # `aws configure list` does not guarantee this file exists.
        if not os.path.isfile(os.path.expanduser('~/.aws/credentials')):
            return (False, '~/.aws/credentials does not exist.' + help_str)
        try:
            output = _run_output('aws configure list')
        except subprocess.CalledProcessError:
            return False, (
                'AWS CLI is not installed properly.'
                ' Run the following commands under sky folder:'
                # TODO(zhwu): after we publish sky to pypi,
                # change this to `pip install sky[aws]`
                '\n     $ pip install .[aws]'
                '\n   Credentials may also need to be set.' + help_str)
        # Configured correctly, the AWS output should look like this:
        #   ...
        #   access_key     ******************** shared-credentials-file
        #   secret_key     ******************** shared-credentials-file
        #   ...
        # Otherwise, one or both keys will show as '<not set>'.
        lines = output.split('\n')
        if len(lines) < 2:
            return False, 'AWS CLI output invalid.'
        access_key_ok = False
        secret_key_ok = False
        for line in lines[2:]:
            line = line.lstrip()
            if line.startswith('access_key'):
                if '<not set>' not in line:
                    access_key_ok = True
            elif line.startswith('secret_key'):
                if '<not set>' not in line:
                    secret_key_ok = True
        if access_key_ok and secret_key_ok:
            return True, None
        return False, 'AWS credentials is not set.' + help_str

    def get_credential_file_mounts(self) -> Dict[str, str]:
        return {
            f'~/.aws/{filename}': f'~/.aws/{filename}'
            for filename in _CREDENTIAL_FILES
        }

    def instance_type_exists(self, instance_type):
        return service_catalog.instance_type_exists(instance_type, clouds='aws')

    def region_exists(self, region: str) -> bool:
        return service_catalog.region_exists(region, 'aws')
