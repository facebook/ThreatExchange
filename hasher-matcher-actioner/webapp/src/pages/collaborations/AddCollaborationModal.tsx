/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */
import {getValue} from '@testing-library/user-event/dist/utils';
import React, {useContext, useEffect, useState} from 'react';
import {
  Modal,
  Container,
  Row,
  Form,
  Col,
  InputGroup,
  Button,
} from 'react-bootstrap';
import {Link} from 'react-router-dom';
import {addNewCollab, fetchAllCollabSchemas} from '../../Api';
import {NotificationsContext} from '../../AppWithNotifications';
import PillBox from '../../components/PillBox';
import {
  CollabSchema,
  CollabSchemaFieldType,
} from '../../messages/CollabMessages';
import {humanizeClassName} from '../settings/ExchangesTab';

type AddCollaborationModalProps = {
  show: boolean;
  onHide: () => void;
  didAdd: () => void;
};

type FieldProps = {
  type: CollabSchemaFieldType;
  name: string;
  value: any;
  onChange: (value: any) => void;
};
function Field({type, name, value, onChange}: FieldProps) {
  let control = (
    <Form.Control
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
    />
  );
  if (type === 'int') {
    control = (
      <Form.Control
        onChange={e => onChange(parseInt(e.target.value, 10))}
        value={value}
        type="text"
      />
    );
  } else if (type === 'bool') {
    control = (
      <Form.Check checked={!!value} onChange={() => onChange(!value)} />
    );
  } else if (type !== 'str') {
    // Must be complex type...
    if (type.type === 'enum') {
      control = (
        <Form.Control
          as="select"
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            onChange(e.target.value)
          }>
          <option>Open this select menu</option>
          {type.possible_values?.map(possible_value => (
            <option key={possible_value} value={possible_value}>
              {possible_value}
            </option>
          ))}
        </Form.Control>
      );
    } else {
      // Must be set..
      control = (
        <PillBox
          handleNewTagAdd={tag => {
            if (!value) {
              onChange([tag]);
            } else if (value.indexOf(tag) === -1) {
              onChange(value.concat([tag]));
            }
          }}
          handleTagDelete={tag => {
            if (value.indexOf(tag) !== -1) {
              onChange(value.filter((x: string) => x !== tag));
            }
          }}
          pills={value || []}
          placeholder="Add values..."
        />
      );
    }
  }

  return (
    <Form.Group className="mb-3" controlId="">
      <Form.Label>{name}</Form.Label>
      {control}
    </Form.Group>
  );
}

export default function AddCollaborationModal({
  show,
  onHide,
  didAdd,
}: AddCollaborationModalProps): JSX.Element {
  const [existingSchemas, setExistingSchemas] = useState<
    Record<string, CollabSchema>
  >({});
  const [collabClassName, setCollabClassName] = useState<string>();
  const [schema, setSchema] = useState<CollabSchema>();
  const [fieldValues, setFieldValues] = useState<Record<string, any>>({});

  const notifications = useContext(NotificationsContext);

  // Load all existing schemas.
  useEffect(() => {
    fetchAllCollabSchemas().then(setExistingSchemas);
  }, []);

  const handleAdd = () => {
    if (collabClassName === undefined) {
      notifications.error({message: 'Must select a collab type.'});
      return;
    }

    addNewCollab(collabClassName, fieldValues).then(() => {
      setCollabClassName(undefined);
      setSchema({});
      setFieldValues({});
      notifications.success({message: 'Added config'});
      didAdd();
    });
  };

  return (
    <Modal show={show} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Add a new Collaboration Config</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Container>
          <Row>
            <Col>
              <p>Select from the following collab class types.</p>
              <p>
                {Object.keys(existingSchemas).length === 0 ? (
                  <p>
                    No Signal Exchange APIs enabled. Go to{' '}
                    <Link to="/settings/exchanges">Settings</Link> and add one.
                  </p>
                ) : (
                  Object.entries(existingSchemas).map(
                    ([className, thisSchema]) => (
                      <Button
                        key={className}
                        variant="link"
                        onClick={() => {
                          setFieldValues({});
                          setCollabClassName(className);
                          setSchema(thisSchema);
                        }}>
                        {humanizeClassName(className)},
                      </Button>
                    ),
                  )
                )}
              </p>
            </Col>
          </Row>
          <Row>
            <Col>
              {collabClassName === undefined ? null : (
                <h2>{humanizeClassName(collabClassName)}</h2>
              )}
            </Col>
          </Row>
          <Row>
            <Col>
              {schema === undefined
                ? null
                : Object.entries(schema).map(([fieldName, fieldType]) => (
                    <Field
                      key={fieldName}
                      type={fieldType}
                      name={fieldName}
                      value={fieldValues[fieldName]}
                      onChange={newValue => {
                        const newFieldValues = {...fieldValues};
                        newFieldValues[fieldName] = newValue;
                        setFieldValues(newFieldValues);
                      }}
                    />
                  ))}
            </Col>
          </Row>
        </Container>
      </Modal.Body>
      <Modal.Footer>
        <Button size="lg" onClick={handleAdd}>
          Add
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
