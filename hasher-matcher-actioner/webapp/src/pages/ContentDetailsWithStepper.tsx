/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useEffect, useState} from 'react';
import {Button, Col, Container, Row, Spinner} from 'react-bootstrap';
import {Link, useParams} from 'react-router-dom';
import {fetchContentPipelineProgress} from '../Api';
import ContentPreview from '../components/ContentPreview';
import ContentProgressStepper from '../components/ContentProgressStepper';
import {getContentTypeForString} from '../utils/constants';
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
  const [contentType, setContentType] = useState<string | null>(null);
  const [contentPreviewURL, setContentPreviewURL] = useState<string | null>(
    null,
  );

  const [pollBuster, setPollBuster] = useState(1);

  // Stage Times
  const [submittedAt, setSubmittedAt] = useState<Date>();
  const [hashedAt, setHashedAt] = useState<Date>();
  const [matchedAt, setMatchedAt] = useState<Date>();
  const [actionEvaluatedAt, setActionEvaluatedAt] = useState<Date>();
  const [actionPerformedAt, setActionPerformedAt] = useState<Date>();

  // // Stage Details
  // const [additionalFields, setAdditionalFields] = useState([]);
  // const [hashResults, setHashResults] = useState({});
  // const [matchResults, setMatchResults] = useState({});
  // const [actionEvaluationResults, setActionEvaluationResults] = useState([]);
  // const [actionPerformResults, setActionPerformResults] = useState([]);

  useEffect(() => {
    // This effect is rerun every time the value of poll buster changes.
    fetchContentPipelineProgress(id).then(pipelineProgress => {
      setContentType(pipelineProgress.content_type);
      setContentPreviewURL(pipelineProgress.content_preview_url);

      // Handle date times
      setSubmittedAt(toDate(pipelineProgress.submitted_at));
      setHashedAt(toDate(pipelineProgress.hashed_at));
      setMatchedAt(toDate(pipelineProgress.matched_at));
      setActionEvaluatedAt(toDate(pipelineProgress.action_evaluated_at));
      setActionPerformedAt(toDate(pipelineProgress.action_performed_at));

      if (pipelineProgress.action_performed_at === null) {
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
              contentType={getContentTypeForString(contentType as string)}
              url={contentPreviewURL}
            />
          ) : null}
        </Col>
        <Col md={{span: 6}}>
          {submittedAt ? (
            <ContentProgressStepper
              submittedAt={submittedAt as Date}
              hashedAt={hashedAt}
              matchedAt={matchedAt}
              actionEvaluatedAt={actionEvaluatedAt}
              actionPerformedAt={actionPerformedAt}
            />
          ) : (
            getStepperLoadingPane()
          )}

          <hr />

          <Container>
            <Row>
              <Col className="mt-2" xs={{offset: 1, span: 8}}>
                <Link to={`/matches/${id}`}>Go to Content Details Page</Link>
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
        </Col>
      </Row>
    </FixedWidthCenterAlignedLayout>
  );
}
