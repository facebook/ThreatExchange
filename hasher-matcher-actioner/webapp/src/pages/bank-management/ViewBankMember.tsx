/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {
  Row,
  Col,
  ResponsiveEmbed,
  Table,
  Button,
  Container,
  Modal,
  Alert,
} from 'react-bootstrap';
import {useParams, Link} from 'react-router-dom';

import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import {BankMemberWithSignals} from '../../messages/BankMessages';
import Loader from '../../components/Loader';
import {fetchBankMember, removeBankMember} from '../../Api';
import {ContentType} from '../../utils/constants';
import {BlurImage, BlurVideo} from '../../utils/MediaUtils';
import {
  CopyableTextField,
  CopyableHashField,
} from '../../utils/TextFieldsUtils';
import ReturnTo from '../../components/ReturnTo';
import {MediaUnavailablePreview} from './Members';

function NoSignalsYet() {
  return (
    <Container>
      <Row>
        <Col>
          <p className="lead">
            No signals have been extracted or provided for this member yet.
          </p>
        </Col>
      </Row>
    </Container>
  );
}

type SignalDetailsProps = {
  signalId: string;
  signalType: string;
  signalValue: string;
};

function SignalDetails({
  signalId,
  signalType,
  signalValue,
}: SignalDetailsProps): JSX.Element {
  return (
    <div>
      <Table>
        <tbody>
          <tr>
            <td>Signal Type:</td>
            <td>{signalType}</td>
          </tr>
          <tr>
            <td>Signal Value:</td>
            <CopyableHashField text={signalValue} />
          </tr>
        </tbody>
      </Table>
    </div>
  );
}

export default function ViewBankMember(): JSX.Element {
  const {bankMemberId} = useParams<{bankMemberId: string}>();
  const [showConfirmModal, setShowConfirmModal] = useState<boolean>(false);

  const [member, setMember] = useState<BankMemberWithSignals>();
  const [pollBuster, setPollBuster] = useState<number>(1);

  useEffect(() => {
    fetchBankMember(bankMemberId).then(setMember);
  }, [pollBuster]);

  const returnURL = member
    ? `/banks/bank/${member.bank_id}/${
        member.content_type === ContentType.Video ? 'video' : 'photo'
      }-memberships`
    : '/';

  const removeMember = () => {
    removeBankMember(bankMemberId).then(() => {
      setShowConfirmModal(false);
      setPollBuster(pollBuster + 1);
    });
  };

  return (
    <FixedWidthCenterAlignedLayout>
      <Row>
        <Col className="my-4">
          <ReturnTo to={returnURL}>Back to Members</ReturnTo>
        </Col>
      </Row>
      <Row>
        <Col xs={{span: 8}}>
          <h2>Bank Member</h2>
        </Col>
        <Col xs={{span: 4}} className="text-right">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setPollBuster(pollBuster + 1)}>
            Refresh
          </Button>{' '}
          {member && !member.is_removed ? (
            <Button
              size="sm"
              variant="danger"
              onClick={() => setShowConfirmModal(true)}>
              Delete Member
            </Button>
          ) : null}
        </Col>
      </Row>
      <Row />
      {member === undefined ? (
        <Row>
          <Col>
            <Loader />
          </Col>
        </Row>
      ) : (
        <Row>
          <Col md={{span: 6}}>
            {member.is_media_unavailable ? (
              <MediaUnavailablePreview />
            ) : (
              <ResponsiveEmbed aspectRatio="4by3">
                {member.content_type === ContentType.Video ? (
                  <BlurVideo src={member.preview_url!} />
                ) : (
                  <BlurImage src={member.preview_url!} />
                )}
              </ResponsiveEmbed>
            )}
          </Col>
          <Col md={{span: 6}}>
            <Container>
              <Row>
                <Col>
                  <h3>Member Details</h3>
                </Col>
              </Row>
              {member.is_removed ? (
                <Row>
                  <Col>
                    <Alert variant="warning">
                      <Alert.Heading>
                        Member is marked as removed!
                      </Alert.Heading>
                      <p>
                        This member is marked as removed. Signals from this
                        member are no longer going to be used for to find
                        similar content.
                      </p>

                      <p>
                        You can add the member again from the{' '}
                        <Link to={returnURL}>bank memberships</Link> page.
                      </p>
                    </Alert>
                  </Col>
                </Row>
              ) : null}
            </Container>
            <Table>
              <tbody>
                <tr>
                  <td>Member ID:</td>
                  <td>
                    <CopyableTextField text={member.bank_member_id} />
                  </td>
                </tr>
                <tr>
                  <td>Notes:</td>
                  <td>{member.notes}</td>
                </tr>
              </tbody>
            </Table>
            <Container>
              <Row>
                <Col>
                  <h3>Signals</h3>
                </Col>
              </Row>
            </Container>
            {member.signals.length === 0 ? (
              <NoSignalsYet />
            ) : (
              member.signals.map(signal => (
                <SignalDetails
                  signalId={signal.signal_id}
                  signalType={signal.signal_type}
                  signalValue={signal.signal_value}
                />
              ))
            )}
          </Col>
        </Row>
      )}
      <Modal show={showConfirmModal} onHide={() => setShowConfirmModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Remove the BankMember </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>
            Are you sure you want to remove this bank member? Once the index
            rebuilds, HMA will stop matching against this member.
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => setShowConfirmModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={removeMember}>
            Yes, Remove this Member
          </Button>
        </Modal.Footer>
      </Modal>
    </FixedWidthCenterAlignedLayout>
  );
}
