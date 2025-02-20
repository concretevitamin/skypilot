Installation
============

Install SkyPilot using pip:

.. code-block:: console

  $ # SkyPilot requires python >= 3.6 and < 3.10.
  $ git clone ssh://git@github.com/skypilot-org/skypilot.git
  $ cd skypilot

  $ # Recommended: use a new conda env to avoid package conflicts.
  $ conda create -n sky python=3.7
  $ conda activate sky

  $ pip install ".[all]"
  $ # To install AWS dependencies only:
  $ # pip install ".[aws]"

SkyPilot currently supports three major cloud providers: AWS, GCP, and Azure.  If you
only have access to certain clouds, use any combination of
:code:`".[aws,azure,gcp]"` (e.g., :code:`".[aws,gcp]"`) to reduce the
dependencies installed.

.. note::

    For Macs, macOS >= 10.15 is required to install SkyPilot. Apple Silicon-based devices (e.g. Apple M1) must run :code:`conda install grpcio` prior to installing SkyPilot.

.. note::

    As an alternative to installing SkyPilot on your laptop, we also provide a Docker image as a quick way to try out SkyPilot. See instructions below on running SkyPilot :ref:`in a container <docker-image>`.

.. _cloud-account-setup:

Cloud account setup
-------------------

Configure access to at least one cloud:

**AWS**

To get the **AWS access key** required by :code:`aws configure`, please go to the `AWS IAM Management Console <https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/security_credentials>`_ and click on the "Access keys" dropdown (detailed instructions `here <https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey>`_). The **Default region name [None]:** and **Default output format [None]:** fields are optional and can be left blank to choose defaults.

.. code-block:: console

  $ # Install boto
  $ pip install boto3

  $ # Configure your AWS credentials
  $ aws configure

**GCP**

.. code-block:: console

  $ pip install google-api-python-client
  $ conda install -c conda-forge google-cloud-sdk

  $ gcloud init

  $ # Run this if you don't have a credentials file.
  $ # This will generate ~/.config/gcloud/application_default_credentials.json.
  $ gcloud auth application-default login

If running :code:`conda install -c conda-forge google-cloud-sdk` produces the error *"RemoveError: 'requests' is a dependency of conda and cannot be removed from conda's operating environment"*, try :code:`conda update --force conda` first and rerun the command.

Note: if you encounter *Authorization Error (Error 400: invalid_request)* with the url generated by :code:`gcloud auth login`, try installing the latest version of the `Google Cloud SDK <https://cloud.google.com/sdk/docs/install>`_ (e.g., with :code:`conda install -c conda-forge google-cloud-sdk`) on **your local machine** (which opened the browser) and rerun the command.

**Azure**

.. code-block:: console

  $ # Login
  $ az login
  $ # Set the subscription to use
  $ az account set -s <subscription_id>

Hint: run ``az account subscription list`` to get a list of subscription IDs under your account.

**Verifying cloud setup**

After configuring the desired clouds, you can optionally run :code:`sky check` to verify that credentials are correctly set up:

.. code-block:: console

  $ sky check

This will produce a summary like:

.. code-block:: text

  Checking credentials to enable clouds for SkyPilot.
    AWS: enabled
    GCP: enabled
    Azure: enabled

  SkyPilot will use only the enabled clouds to run tasks. To change this, configure cloud credentials, and run sky check.

Requesting quotas for first time users
--------------------------------------

If your cloud account has not been used to launch instances before, the
respective quotas are likely set to zero or a low limit.  This is especially
true for GPU instances.

Please follow :ref:`Requesting Quota Increase` to check quotas and request quota
increases before proceeding.

.. _docker-image:

Quick alternative: trying in Docker
------------------------------------------------------

As a **quick alternative to installing SkyPilot on your laptop**, we also provide a Docker image with SkyPilot and
its dependencies installed for users to quickly try out SkyPilot. You can simply run:

.. code-block:: console

  $ docker run -td --name sky --rm -v "$HOME/.sky:/root/.sky:rw" -v "$HOME/.aws:/root/.aws:rw" -v "$HOME/.config/gcloud:/root/.config/gcloud:rw" -v "$HOME/.azure:/root/.azure:rw" public.ecr.aws/a9w6z7w5/sky:latest
  $ docker exec -it sky /bin/bash

If your cloud CLIs are already setup, your credentials will be mounted to the
container and you can proceed to :ref:`Quickstart <Quickstart>`. Else you can
follow the instructions in :ref:`Cloud account setup <cloud-account-setup>`
inside the container to setup your cloud accounts.

If you exit from the shell in the container, the container will keep running
in the background. You can start a new shell with :code:`docker exec -it sky /bin/bash`.

Once you are done with experimenting with sky, remember to delete any clusters
and storage resources you may have created using the following commands:

.. code-block:: console

  # Run inside the container

  $ sky down -a -y
  $ sky storage delete -a -y

Finally, you can stop the container with:

.. code-block:: console

  $ docker stop sky
