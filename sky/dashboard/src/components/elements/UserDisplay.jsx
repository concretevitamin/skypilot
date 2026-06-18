import React from 'react';
import Link from 'next/link';
import PropTypes from 'prop-types';
import { getUserLink, isServiceAccount } from '@/utils/userUtils';

/**
 * ServiceAccountBadge component - A reusable badge for service accounts
 */
const ServiceAccountBadge = () => (
  <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded font-medium ml-1">
    SA
  </span>
);

/**
 * UserDisplay component - Displays a user with clickable link and SA badge if applicable
 *
 * @param {Object} props
 * @param {string} props.username - The display name of the user
 * @param {string} props.userHash - The user hash (used for routing and SA detection)
 * @param {string} [props.className] - Additional CSS classes for the container
 * @param {string} [props.linkClassName] - Additional CSS classes for the link
 * @param {boolean} [props.showBadge=true] - Whether to show the SA badge for service accounts
 * @param {Function} [props.onClick] - When provided, clicking the username invokes this
 *   callback (with the username) instead of navigating to the user's page. Used to
 *   turn the username into a filter, e.g. on the Jobs page.
 */
export const UserDisplay = ({
  username,
  userHash,
  className = 'flex items-center gap-1',
  linkClassName = 'text-gray-700 hover:text-blue-600 hover:underline',
  showBadge = true,
  onClick = null,
}) => {
  const isServiceAcc = isServiceAccount(userHash);
  const userUrl = getUserLink(userHash);

  return (
    <div className={className}>
      {onClick ? (
        <button
          type="button"
          onClick={() => onClick(username)}
          className={`${linkClassName} bg-transparent border-none p-0 cursor-pointer text-left`}
          title={`Filter by ${username}`}
        >
          {username}
        </button>
      ) : (
        <Link href={userUrl} className={linkClassName}>
          {username}
        </Link>
      )}
      {showBadge && isServiceAcc && <ServiceAccountBadge />}
    </div>
  );
};

UserDisplay.propTypes = {
  username: PropTypes.string.isRequired,
  userHash: PropTypes.string,
  className: PropTypes.string,
  linkClassName: PropTypes.string,
  showBadge: PropTypes.bool,
  onClick: PropTypes.func,
};

export default UserDisplay;
