/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useContext} from 'react';
import {
  Button,
  ToggleButtonGroup,
  Col,
  Container,
  Dropdown,
  DropdownButton,
  Row,
  ToggleButton,
  Form,
} from 'react-bootstrap';
import {IonIcon} from '@ionic/react';
import {ellipsisHorizontal} from 'ionicons/icons';
import {useFormik} from 'formik';

import '../../styles/_settings.scss';
import type {ActionRule, Label} from '../../messages/ActionMessages';
import {ActionPerformer} from '../../pages/settings/ActionPerformerSettingsTab';
import {ConfirmationsContext} from '../../AppWithConfirmations';
import PillBox from '../PillBox';

function getCurrentAction(
  allActions: ActionPerformer[],
  actionRule: ActionRule,
): ActionPerformer | undefined {
  return allActions.find(_ => _.name === actionRule.action_label.value);
}

function getActionView(
  allActions: ActionPerformer[],
  actionRule: ActionRule,
): JSX.Element {
  if (
    allActions === undefined ||
    allActions.length === 0 ||
    actionRule.action_label === undefined ||
    actionRule.action_label.value === undefined ||
    actionRule.action_label.value.length === 0
  ) {
    return <span>&mdash;</span>;
  }
  const actionPerformer = getCurrentAction(allActions, actionRule);

  if (actionPerformer) {
    return <span>{actionPerformer.name}</span>;
  }
  return <span>&mdash;</span>;
}

type Input = {
  actionRule: ActionRule;
  actions: ActionPerformer[];
  onDeleteActionRule: (name: string, deleteFromUIOnly: boolean) => void;
  onUpdateActionRule: (oldName: string, updatedActionRule: ActionRule) => void;
  nameIsUnique: (newName: string, oldName: string) => boolean;
  forceEditing?: boolean;
};

type ActionRuleForm = {
  actionRuleName: string | undefined;
  actionName: string | undefined;
  source: string | undefined;
  labels: string[];
};

/**
 * A viewer and an editor for action rules. Note that the backend representation
 * and the frontend view in this case are dramatically different. If we ever
 * support must_not_have_labels, this is where the change needs to be made.
 */
export default function ActionRuleRow({
  actionRule,
  actions,
  onDeleteActionRule,
  onUpdateActionRule,
  nameIsUnique,
  forceEditing,
}: Input): JSX.Element {
  const [editing, setEditing] = useState(forceEditing); // Parent can recommend that we start in the editing mode.

  const confirmations = useContext(ConfirmationsContext);
  const showDeleteConfirmation = () => {
    confirmations.confirm({
      message: `Please confirm you want to delete the action rule named "${actionRule.name}"`,
      ctaText: 'Yes, delete this Action Rule',
      ctaVariant: 'danger',
      onConfirm: () => onDeleteActionRule(actionRule.name, false),
      onCancel: () => undefined,
    });
  };

  const actionPerformer = getCurrentAction(actions, actionRule);

  // Although this is not enforced, an action rule SHOULD only have a single
  // source classification.
  const sourceLabels = actionRule.must_have_labels.filter(
    label => label.key === 'BankSourceClassification',
  );
  const hasSourceLabel = sourceLabels.length > 0;

  // Even though there may be more than one source classification, only one is
  // used.
  const source: string | undefined = hasSourceLabel
    ? sourceLabels[0].value
    : undefined;

  const classificationLabels = actionRule.must_have_labels
    .filter(_ => _.key === 'Classification')
    .map(_ => _.value);

  const validate = (values: ActionRuleForm) => {
    // Formik style validator
    const errors: Partial<ActionRuleForm> = {};

    if (!values.actionName) {
      errors.actionName = 'Required';
    }

    if (values.actionRuleName) {
      if (!nameIsUnique(values.actionRuleName, actionRule.name)) {
        errors.actionRuleName = 'Name is already Taken';
      }
    } else {
      errors.actionRuleName = 'Required';
    }

    if (!values.source) {
      errors.source = 'Required';
    }
    console.log(errors);
    return errors;
  };

  const formik = useFormik({
    initialValues: {
      actionRuleName: actionRule.name,
      actionName: actionPerformer?.name,
      source,
      labels: classificationLabels,
    },
    validate,
    onSubmit: values => {
      // Convert to server side representations:
      const labelClassifications = values.labels.map(_ => ({
        key: 'Classification',
        value: _,
      }));

      const payload: ActionRule = {
        name: values.actionRuleName,

        // formik validate() will always ensure actionName is defined.
        action_label: {key: 'Action', value: values.actionName as string},

        must_have_labels: [
          {
            key: 'BankSourceClassification',
            value: values.source || 'bnk',
          },
        ].concat(labelClassifications),

        // Not supported yet
        must_not_have_labels: [],
      };
      onUpdateActionRule(actionRule.name, payload);
      setEditing(false);
    },
  });

  return (
    <tr>
      <td>
        <Container>
          <Row>
            <Col>
              <div>
                <small className="text-secondary">Action rule name</small>
              </div>
              <Form.Control
                readOnly={!editing}
                plaintext={!editing}
                id="actionRuleName"
                size="sm"
                type="text"
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                isInvalid={formik.touched && !!formik.errors.actionRuleName}
                isValid={
                  formik.touched.actionRuleName && !formik.errors.actionRuleName
                }
                value={formik.values.actionRuleName}
              />
              {formik.errors.actionRuleName ? (
                <Form.Control.Feedback type="invalid">
                  {formik.errors.actionRuleName}
                </Form.Control.Feedback>
              ) : null}
            </Col>
          </Row>
          <Row className="pt-4">
            <Col>
              <div>
                <small className="text-secondary">Action taken</small>
              </div>
              {editing ? (
                <Form.Control
                  id="actionName"
                  as="select"
                  size="sm"
                  onChange={formik.handleChange}
                  isInvalid={
                    formik.touched.actionName && !!formik.errors.actionName
                  }
                  isValid={
                    formik.touched.actionName && !formik.errors.actionName
                  }
                  defaultValue={actionPerformer?.name}>
                  <option>Select an action</option>
                  {actions.map(action => (
                    <option key={action.name} id={action.name}>
                      {action.name}
                    </option>
                  ))}
                </Form.Control>
              ) : (
                getActionView(actions, actionRule)
              )}
              {editing &&
              formik.touched.actionName &&
              formik.errors.actionName ? (
                <Form.Control.Feedback type="invalid">
                  {formik.errors.actionName}
                </Form.Control.Feedback>
              ) : null}
            </Col>
          </Row>
        </Container>
      </td>
      <td className="action-rule-classification-column">
        <Container>
          <Row>
            <Col>
              <div className="text-secondary">
                <small>Matched against</small>
              </div>
              <ToggleButtonGroup
                onChange={val => formik.setFieldValue('source', val)}
                name="source-classification-toggle"
                type="radio">
                {[
                  {serverRepr: 'bnk', label: 'Your Banks'},
                  {serverRepr: 'te', label: 'ThreatExchange Hashes'},
                ].map(obj => (
                  <ToggleButton
                    size="sm"
                    key={obj.serverRepr}
                    disabled={!editing}
                    type="radio"
                    variant={
                      obj.serverRepr === formik.values.source
                        ? 'secondary'
                        : 'outline-secondary'
                    }
                    name={obj.serverRepr}
                    value={obj.serverRepr}
                    checked={obj.serverRepr === formik.values.source}>
                    {obj.label}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
              {formik.touched.source && formik.errors.source ? (
                <Form.Control.Feedback
                  // Without an actual Form.Control as a sibling, the feedback
                  // div is hidden. Show it explicitly!
                  style={{display: 'block'}}
                  type="invalid">
                  {formik.errors.source}
                </Form.Control.Feedback>
              ) : null}
            </Col>
          </Row>
          <Row className="pt-2">
            <Col>
              <div className="text-secondary">
                <small>Has labels</small>
              </div>
              <PillBox
                readOnly={!editing}
                pills={formik.values.labels}
                handleNewTagAdd={tag => {
                  const alreadyExists =
                    formik.values.labels.indexOf(tag) !== -1;
                  if (!alreadyExists) {
                    formik.setFieldValue(
                      'labels',
                      formik.values.labels.concat([tag]),
                    );
                  }
                }}
                handleTagDelete={tag => {
                  const alreadyExists =
                    formik.values.labels.indexOf(tag) !== -1;
                  if (alreadyExists) {
                    formik.setFieldValue(
                      'labels',
                      formik.values.labels.filter(x => x !== tag),
                    );
                  }
                }}
              />
            </Col>
          </Row>
        </Container>
      </td>
      <td className="text-right">
        {editing ? (
          <>
            <Button size="sm" onClick={formik.submitForm}>
              Save
            </Button>{' '}
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                setEditing(false);
                formik.resetForm();
              }}>
              Cancel
            </Button>
          </>
        ) : (
          <DropdownButton
            title={<IonIcon icon={ellipsisHorizontal} />}
            menuAlign="right"
            variant="outline-secondary"
            className="no-caret">
            <Dropdown.Item onClick={() => setEditing(true)}>Edit</Dropdown.Item>
            <Dropdown.Divider />
            <Dropdown.Item
              className="text-danger"
              onClick={showDeleteConfirmation}>
              Delete
            </Dropdown.Item>
          </DropdownButton>
        )}
      </td>
    </tr>
  );
}

ActionRuleRow.defaultProps = {
  forceEditing: false,
};
