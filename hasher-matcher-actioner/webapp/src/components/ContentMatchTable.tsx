/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, useEffect, useContext} from 'react';
import {Col, Collapse, Row, Table} from 'react-bootstrap';
import PropTypes from 'prop-types';
import Spinner from 'react-bootstrap/Spinner';
import {Link} from 'react-router-dom';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Tooltip from 'react-bootstrap/Tooltip';

import {fetchMatchDetails, MatchDetails} from '../Api';
import {CopyableHashField, CopyableTextField} from '../utils/TextFieldsUtils';
import {timeAgo} from '../utils/DateTimeUtils';
import OpinionTableCell from './OpinionTableCell';
import {NotificationsContext} from '../AppWithNotifications';

type SignalDetailsCellProps = {
  match: MatchDetails;
};

function SignalDetailsCell({match}: SignalDetailsCellProps): JSX.Element {
  const notifications = useContext(NotificationsContext);
  // Elected to keep this component in same file for now as it is subject to a fair amout of thrash
  // as TE signals are refactored to use banks.
  return (
    <>
      {match.te_signal_details && match.te_signal_details.length ? (
        <>
          <h5>Dataset Membership</h5>
          <Table title="Datasets">
            <thead>
              <tr>
                <th>Dataset ID</th>
                <th>Opinion</th>
                <th>Tags</th>
              </tr>
            </thead>
            {match.te_signal_details.map(details => (
              <tbody key={match.signal_id + details.privacy_group_id}>
                <tr>
                  <td>
                    <Link to="/settings/threatexchange">
                      {details.privacy_group_id}
                    </Link>
                  </td>
                  <td>
                    <OpinionTableCell
                      privacyGroupId={details.privacy_group_id}
                      signalId={match.signal_id}
                      signalSource={match.signal_source}
                      opinion={details.opinion}
                      pendingOpinionChange={details.pending_opinion_change}
                      setShowToast={() =>
                        notifications.success({
                          header: 'Submitted',
                          message:
                            'Please wait for the requested change to propagate',
                        })
                      }
                    />
                  </td>
                  <td>{details.tags.join(', ')}</td>
                </tr>
              </tbody>
            ))}
          </Table>
        </>
      ) : null}
      {match.banked_signal_details && match.banked_signal_details.length ? (
        <>
          <h5>Bank Membership</h5>
          <Table title="Banks">
            <thead>
              <tr>
                <th>Bank ID</th>
                <th>Member ID</th>
              </tr>
            </thead>
            {match.banked_signal_details.map(details => (
              <tbody key={match.signal_id + details.bank_member_id}>
                <tr>
                  <td>
                    <Link to={`/banks/bank/${details.bank_id}/bank-details`}>
                      {details.bank_id}
                    </Link>
                  </td>
                  <td>
                    <Link to={`/banks/member/${details.bank_member_id}`}>
                      {details.bank_member_id}
                    </Link>
                  </td>
                </tr>
              </tbody>
            ))}
          </Table>
        </>
      ) : null}
    </>
  );
}

export default function ContentMatchTable({
  contentKey,
}: {
  contentKey: string;
}): JSX.Element {
  const [matchesDetails, setMatchesDetails] = useState<MatchDetails[]>();

  useEffect(() => {
    fetchMatchDetails(contentKey).then(matches => {
      setMatchesDetails(matches.match_details);
    });
  }, [contentKey]);

  return (
    <>
      <Spinner
        hidden={matchesDetails !== null}
        animation="border"
        role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={matchesDetails !== null}>
        <Row>
          <Col md={12}>
            <h3>Matched Signals</h3>
            <Table responsive striped bordered title="Matches">
              <thead>
                <tr>
                  <th>Signal ID</th>
                  <th>Type</th>
                  <th>Signal</th>
                  <th>LastUpdated</th>
                  <OverlayTrigger
                    overlay={
                      <Tooltip id={`tooltip-signal-details-${contentKey}`}>
                        This column is current state for each signal. It may
                        have been different when this signal was originally
                        matched.
                      </Tooltip>
                    }>
                    <th>Current Signal Details</th>
                  </OverlayTrigger>
                </tr>
              </thead>
              <tbody>
                {matchesDetails && matchesDetails.length ? (
                  matchesDetails.map(match => (
                    <tr key={match.signal_id}>
                      <td>
                        <CopyableTextField text={match.signal_id} />
                      </td>
                      <td>{match.signal_type}</td>
                      <CopyableHashField text={match.signal_hash} />
                      <td>{timeAgo(match.updated_at)}</td>
                      <td>{SignalDetailsCell({match})}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No Matches found for this Content.</td>
                  </tr>
                )}
              </tbody>
            </Table>
          </Col>
        </Row>
      </Collapse>
    </>
  );
}

ContentMatchTable.propTypes = {
  contentKey: PropTypes.string,
};

ContentMatchTable.defaultProps = {
  contentKey: undefined,
};
