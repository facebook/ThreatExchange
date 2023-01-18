/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React from 'react';
import {Col, Container, Row} from 'react-bootstrap';
import classNames from 'classnames';
import Spinner from 'react-bootstrap/Spinner';

import '../styles/_progress-stepper.scss';
import {timeOnlyIfToday} from '../utils/DateTimeUtils';

enum StepperStatus {
  InProgress = 'in-progress',
  Pending = 'pending',
  Completed = 'completed',
}

enum StepperStages {
  Submitted = 'submitted',
  Hashed = 'hashed',
  Matched = 'matched',
  ActionEvaluated = 'evaluated',
  ActionPerformed = 'performed',
}

type StepperChannelSegmentProps = {
  status: StepperStatus;
  position: 'first' | 'last' | 'in-between';
};

/**
 * Represents the channel on the left side of a stepper. Made of 3 parts. The
 * lead-in channel, the bullet and the lead-out channel. Based on the status of
 * the channel segment, changes the visibility and appearance.
 */
function StepperChannelSegment({status, position}: StepperChannelSegmentProps) {
  return (
    <Col
      xs={1}
      className={classNames('stepper-channel-segment', status, position)}>
      <div className="lead-in" />
      {status === 'in-progress' ? (
        <Spinner animation="border" variant="success" size="sm" />
      ) : (
        <div className="bullet" />
      )}
      <div className="lead-out" />
    </Col>
  );
}

type StageTitleProps = {
  children: string;
};

/**
 * Used to add padding to the top of the title. The space at the top corresponds
 * to the lead-in portion of the channel segment.
 */
function StageTitle({children}: StageTitleProps) {
  return (
    <div className="stage-title">
      <span>{children}</span>
      <span className="aligner" />
    </div>
  );
}

type StageTimeViewProps = {
  stage: StepperStages;
  completedAt: Date;
};

/**
 * A small component that renders the time a stage was completed. Only add this
 * if the time is actually available.
 */
function StageTimeView({stage, completedAt}: StageTimeViewProps): JSX.Element {
  const label = new Map([
    [StepperStages.Submitted, 'Submitted at'],
    [StepperStages.Hashed, 'Hash Recorded at'],
    [StepperStages.Matched, 'Matched at'],
    [StepperStages.ActionEvaluated, 'Action Evaluated at'],
    [StepperStages.ActionPerformed, 'Action Performed at'],
  ]).get(stage);

  return (
    <div className="stage-time-view">
      <span className="stage-time-label">
        <small>{label}:&nbsp;</small>
      </span>
      <span className="stage-time">
        <small>{timeOnlyIfToday(completedAt)}</small>
      </span>
    </div>
  );
}

/**
 * Given all the timestamps from the pipeline-progress call, identifies the
 * current status.
 */
function getStageFromTimestamps(
  hashedAt?: Date,
  matchedAt?: Date,
  actionEvaluatedAt?: Date,
  actionPerformedAt?: Date,
): StepperStages {
  if (actionPerformedAt instanceof Date) {
    return StepperStages.ActionPerformed;
  }
  if (actionEvaluatedAt instanceof Date) {
    return StepperStages.ActionEvaluated;
  }
  if (matchedAt instanceof Date) {
    return StepperStages.Matched;
  }
  if (hashedAt instanceof Date) {
    return StepperStages.Hashed;
  }

  return StepperStages.Submitted;
}

/**
 * @param currentStage The current stage of the overall stepper
 * @param stage The stage that we are evaluating the status for.
 */
function getStepperStatus(
  currentStage: StepperStages,
  stage: StepperStages,
): StepperStatus {
  const stageNumber: Map<StepperStages, number> = new Map([
    [StepperStages.Submitted, 0],
    [StepperStages.Hashed, 1],
    [StepperStages.Matched, 2],
    [StepperStages.ActionEvaluated, 3],
    [StepperStages.ActionPerformed, 4],
  ]);

  if (
    (stageNumber.get(stage) as number) <=
    (stageNumber.get(currentStage) as number)
  ) {
    return StepperStatus.Completed;
  }
  if (
    (stageNumber.get(stage) as number) + 1 ===
    (stageNumber.get(currentStage) as number)
  ) {
    return StepperStatus.InProgress;
  }
  return StepperStatus.Pending;
}

type ContentProgressStepperProps = {
  submittedAt: Date;
  hashedAt?: Date;
  matchedAt?: Date;
  actionEvaluatedAt?: Date;
  actionPerformedAt?: Date;
};

export default function ContentProgressStepper({
  submittedAt,
  hashedAt,
  matchedAt,
  actionEvaluatedAt,
  actionPerformedAt,
}: ContentProgressStepperProps): JSX.Element {
  const currentStage = getStageFromTimestamps(
    hashedAt,
    matchedAt,
    actionEvaluatedAt,
    actionPerformedAt,
  );

  return (
    <Container className="progress-stepper">
      <Row className="stage">
        <StepperChannelSegment
          position="first"
          status={getStepperStatus(currentStage, StepperStages.Submitted)}
        />{' '}
        <Col xs={11}>
          <StageTitle>Submitted</StageTitle>
          <div className="stage-description">
            All content objects submitted are recorded in our database.
          </div>
          {submittedAt && (
            <StageTimeView
              stage={StepperStages.Submitted}
              completedAt={submittedAt}
            />
          )}
        </Col>
      </Row>
      <Row className="stage">
        <StepperChannelSegment
          position="in-between"
          status={getStepperStatus(currentStage, StepperStages.Hashed)}
        />{' '}
        <Col xs={11}>
          <StageTitle>Hashed</StageTitle>
          <div className="stage-description">
            These objects are then hashed into a variety of formats based on
            your configuration and the content&lsquo;s type.
          </div>
          {hashedAt && (
            <StageTimeView
              stage={StepperStages.Hashed}
              completedAt={hashedAt}
            />
          )}
        </Col>
      </Row>
      <Row className="stage">
        <StepperChannelSegment
          position="in-between"
          status={getStepperStatus(currentStage, StepperStages.Matched)}
        />{' '}
        <Col xs={11}>
          <StageTitle>Matched</StageTitle>
          <div className="stage-description">
            The hashes are then matched against the datasets available from
            threatexchange.
          </div>
          {matchedAt && (
            <StageTimeView
              stage={StepperStages.Matched}
              completedAt={matchedAt}
            />
          )}
        </Col>
      </Row>
      <Row className="stage">
        <StepperChannelSegment
          position="in-between"
          status={getStepperStatus(currentStage, StepperStages.ActionEvaluated)}
        />{' '}
        <Col xs={11}>
          <StageTitle>Needs Actioning</StageTitle>
          <div className="stage-description">
            Your Action Rules then determine whether to perform actions on these
            matches.
          </div>
          {actionEvaluatedAt && (
            <StageTimeView
              stage={StepperStages.ActionEvaluated}
              completedAt={actionEvaluatedAt}
            />
          )}
        </Col>
      </Row>
      <Row className="stage">
        <StepperChannelSegment
          position="last"
          status={getStepperStatus(currentStage, StepperStages.ActionPerformed)}
        />{' '}
        <Col xs={11}>
          <StageTitle>Actioned</StageTitle>
          <div className="stage-description">
            The actions determined in the previous stage are then performed.
          </div>
          {actionPerformedAt && (
            <StageTimeView
              stage={StepperStages.ActionPerformed}
              completedAt={actionPerformedAt}
            />
          )}
        </Col>
      </Row>
    </Container>
  );
}

ContentProgressStepper.defaultProps = {
  hashedAt: undefined,
  matchedAt: undefined,
  actionEvaluatedAt: undefined,
  actionPerformedAt: undefined,
};
