/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, useContext, useEffect} from 'react';
import {
  Row,
  Col,
  ResponsiveEmbed,
  Form,
  Table,
  Button,
  Container,
  Modal,
  Alert,
} from 'react-bootstrap';
import {useParams, Link} from 'react-router-dom';

import {useFormik} from 'formik';
import FixedWidthCenterAlignedLayout from '../layouts/FixedWidthCenterAlignedLayout';
import {ConfirmationsContext} from '../../AppWithConfirmations';
import {BankMemberWithSignals} from '../../messages/BankMessages';
import Loader from '../../components/Loader';
import {fetchBankMember, removeBankMember, updateBankMember} from '../../Api';
import {ContentType} from '../../utils/constants';
import {BlurImage, BlurVideo} from '../../utils/MediaUtils';
import {
  CopyableTextField,
  CopyableHashField,
} from '../../utils/TextFieldsUtils';
import ReturnTo from '../../components/ReturnTo';
import {MediaUnavailablePreview} from './Members';
import PillBox from '../../components/PillBox';

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

type BankMemberEditableAttributesFormProps = {
  notes: string;
  tags: string[];
  handleSubmit: (notes: string, tags: string[]) => void;
};

function BankMemberEditableAttributesForm({
  notes,
  tags,
  handleSubmit,
}: BankMemberEditableAttributesFormProps): JSX.Element {
  const formik = useFormik({
    initialValues: {
      notes,
      tags,
    },
    enableReinitialize: true,
    onSubmit: values => {
      handleSubmit(values.notes, values.tags);
    },
  });

  return (
    <tbody>
      <tr>
        <td>Notes:</td>
        <td>
          <Form.Control
            id="notes"
            as="textarea"
            rows={3}
            placeholder="Optional description or instructions for other admins. Can be added later."
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            isValid={formik.touched.notes && !formik.errors.notes}
            isInvalid={formik.touched.notes && !!formik.errors.notes}
            value={formik.values.notes}
          />
        </td>
      </tr>
      <tr>
        <td>Tags:</td>
        <td>
          <PillBox
            readOnly
            handleNewTagAdd={tag => {
              const alreadyExists = formik.values.tags.indexOf(tag) !== -1;
              if (!alreadyExists) {
                formik.setFieldValue('tags', formik.values.tags.concat([tag]));
              }
            }}
            handleTagDelete={tag => {
              const alreadyExists = formik.values.tags.indexOf(tag) !== -1;
              if (alreadyExists) {
                formik.setFieldValue(
                  'tags',
                  formik.values.tags.filter(x => x !== tag),
                );
              }
            }}
            pills={formik.values.tags}
          />
        </td>
      </tr>
      {formik.dirty ? (
        <tr>
          <td />
          <td>
            <Button onClick={() => formik.submitForm()}>Save Changes</Button>
          </td>
        </tr>
      ) : null}
    </tbody>
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

  const removeMember = () => {
    removeBankMember(bankMemberId).then(() => {
      setPollBuster(pollBuster + 1);
    });
  };

  const handleEditableAttributesSubmit = (notes: string, tags: string[]) => {
    updateBankMember(bankMemberId, notes, tags).then(() => {
      setPollBuster(pollBuster + 1);
    });
  };

  const confirmations = useContext(ConfirmationsContext);
  const confirmDeleteBankMember = () => {
    confirmations.confirm({
      message:
        'Are you sure you want to remove this bank member? Once the index rebuilds, HMA will stop matching against this member.',
      ctaVariant: 'danger',
      ctaText: 'Yes. Remove this Member.',
      onCancel: () => undefined,
      onConfirm: removeMember,
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
              onClick={confirmDeleteBankMember}>
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
              </tbody>
              <BankMemberEditableAttributesForm
                tags={member.bank_member_tags}
                notes={member.notes}
                handleSubmit={handleEditableAttributesSubmit}
              />
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
