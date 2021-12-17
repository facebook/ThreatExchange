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
} from 'react-bootstrap';
import {useParams} from 'react-router-dom';

import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import {BankMemberWithSignals} from '../../messages/BankMessages';
import Loader from '../../components/Loader';
import {fetchBankMember} from '../../Api';
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

  return (
    <FixedWidthCenterAlignedLayout>
      <Row>
        <Col className="my-4">
          <ReturnTo to={returnURL}>Back to Members</ReturnTo>
        </Col>
      </Row>
      <Row>
        <Col>
          <h1>Bank Member</h1>
        </Col>
      </Row>
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
                <Col xs={{span: 10}}>
                  <h3>Member Details</h3>
                </Col>
                <Col xs={{span: 2}}>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setPollBuster(pollBuster + 1)}>
                    Refresh
                  </Button>
                </Col>
              </Row>
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
    </FixedWidthCenterAlignedLayout>
  );
}
