/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useEffect, useState} from 'react';
import {Col, Container, Row, Spinner} from 'react-bootstrap';
import {Link, useParams} from 'react-router-dom';
import {fetchContentPipelineProgress} from '../Api';
import ContentPreview from '../components/ContentPreview';
import ContentProgressStepper from '../components/ContentProgressStepper';
import {ContentType, getContentTypeForString} from '../utils/constants';
import {toDate} from '../utils/DateTimeUtils';

import FixedWidthCenterAlignedLayout from './layouts/FixedWidthCenterAlignedLayout';

const POLL_INTERVAL_IN_SECONDS = 5;

function getStepperLoadingPane(): JSX.Element {
  return (
    <div>
      <h1>
        <Spinner animation="border" /> Loading state for content.
      </h1>
    </div>
  );
}

export default function ContentDetailsWithStepper(): JSX.Element {
  const {id} = useParams<{id: string}>();
  const [contentType, setContentType] = useState(null);
  const [contentPreviewURL, setContentPreviewURL] = useState(null);

  const [pollBuster, setPollBuster] = useState(1);

  // Stage Times
  const [submittedAt, setSubmittedAt] = useState();
  const [hashedAt, setHashedAt] = useState();
  const [matchedAt, setMatchedAt] = useState();
  const [actionEvaluatedAt, setActionEvaluatedAt] = useState();
  const [actionPerformedAt, setActionPerformedAt] = useState();

  // Stage Details
  const [additionalFields, setAdditionalFields] = useState([]);
  const [hashResults, setHashResults] = useState({});
  const [matchResults, setMatchResults] = useState({});
  const [actionEvaluationResults, setActionEvaluationResults] = useState([]);
  const [actionPerformResults, setActionPerformResults] = useState([]);

  useEffect(() => {
    // This effect is rerun every time the value of poll buster changes.
    fetchContentPipelineProgress(id).then(pipelineProgress => {
      setContentType(pipelineProgress.content_type);
      setContentPreviewURL(pipelineProgress.content_preview_url);

      // Handle date times
      setSubmittedAt(
        pipelineProgress.submitted_at && toDate(pipelineProgress.submitted_at),
      );
      setHashedAt(
        pipelineProgress.hashed_at && toDate(pipelineProgress.hashed_at),
      );
      setMatchedAt(
        pipelineProgress.matched_at && toDate(pipelineProgress.matched_at),
      );
      setActionEvaluatedAt(
        pipelineProgress.action_evaluated_at &&
          toDate(pipelineProgress.action_evaluated_at),
      );
      setActionPerformedAt(
        pipelineProgress.action_performed_at &&
          toDate(pipelineProgress.action_performed_at),
      );

      if (pipelineProgress.action_performed_at === undefined) {
        // The pipeline has not yet finished, so setup a poller to call this
        // effect again. If we start storing null records, ie. match produced no
        // results, then we need to revisit how we evaluate that the pipeline is
        // "done".
        setTimeout(() => {
          setPollBuster(pollBuster + 1);
        }, POLL_INTERVAL_IN_SECONDS * 1000);
      }
    });
  }, [pollBuster]);

  return (
    <FixedWidthCenterAlignedLayout title="Progress">
      <Row>
        <Col md={{span: 6}}>
          {contentPreviewURL && contentType ? (
            <ContentPreview
              contentId={id}
              contentType={getContentTypeForString(contentType!)}
              url={contentPreviewURL!}
            />
          ) : null}
        </Col>
        <Col md={{span: 6}}>
          {submittedAt === null ? (
            getStepperLoadingPane()
          ) : (
            <ContentProgressStepper
              submittedAt={submittedAt!}
              hashedAt={hashedAt}
              matchedAt={matchedAt}
              actionEvaluatedAt={actionEvaluatedAt}
              actionPerformedAt={actionPerformedAt}
            />
          )}

          <hr />

          <Container>
            <Row>
              <Col className="mt-2" xs={{offset: 1}}>
                <Link to={`/matches/${id}`}>Go to Content Details Page</Link>
              </Col>
            </Row>
          </Container>
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}
