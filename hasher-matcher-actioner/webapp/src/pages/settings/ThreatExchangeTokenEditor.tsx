/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */
import React, {useState, useContext} from 'react';
import {Accordion, Button, Card, Form} from 'react-bootstrap';
import {IonIcon} from '@ionic/react';
import {chevronUp, chevronDown} from 'ionicons/icons';
import {useFormik} from 'formik';
import {updateThreatExchangeAPIToken} from '../../Api';
import {NotificationsContext} from '../../AppWithNotifications';

type TETokenFormFields = {
  token: string;
};

/**
 * This never fetches the te token from the backend, only updates it if
 * something changed. Applies string validations on the frontend and uses an
 * actual query on the backend before setting it as the value on the backend.
 */
export default function ThreatExchangeTokenEditor(): JSX.Element {
  const [showEditor, setShowEditor] = useState<boolean>(false);
  const notifications = useContext(NotificationsContext);

  const onSubmit = (token: string) => {
    updateThreatExchangeAPIToken(token).then(result => {
      if (result) {
        notifications.success({message: 'ThreatExchange API Token updated!'});
      } else {
        notifications.error({
          message:
            'Malformed or unauthorized API Token. Did not update ThreatExchange API Token.',
        });
      }
    });
  };

  const validateTEToken = (values: TETokenFormFields) => {
    const errors: Partial<TETokenFormFields> = {};

    if (values.token && values.token.indexOf('|') === -1) {
      errors.token =
        'Not a ThreatExchange App Token. Copy one from the link below.';
    }

    if (values.token === '') {
      errors.token = 'ThreatExchange App Token cannot be empty';
    }

    return errors;
  };

  const formik = useFormik({
    initialValues: {
      token: '',
    },
    validate: validateTEToken,
    validateOnChange: true,
    onSubmit: () => undefined,
  });

  return (
    <Card>
      <Accordion>
        <Accordion.Toggle
          eventKey="0"
          as={Card.Header}
          onClick={() => setShowEditor(!showEditor)}
          style={{cursor: 'pointer'}}
          variant="outline-dark">
          Change ThreatExchange Access Token &nbsp;
          <IonIcon
            className="inline-icon"
            icon={showEditor ? chevronUp : chevronDown}
          />
        </Accordion.Toggle>
        <Accordion.Collapse eventKey="0">
          <Card.Body>
            <Form>
              <Form.Group>
                <Form.Label>Enter new ThreatExchange Token</Form.Label>
                <Form.Control
                  id="token"
                  onBlur={formik.handleBlur}
                  isValid={formik.values.token !== '' && !formik.errors.token}
                  isInvalid={!!formik.errors.token}
                  onChange={formik.handleChange}
                  type="text"
                  value={formik.values.token}
                />
                {formik.errors.token ? (
                  <Form.Control.Feedback type="invalid">
                    {formik.errors.token}
                  </Form.Control.Feedback>
                ) : null}
                <Form.Text muted>
                  You can obtain your threatexchange access tokens at{' '}
                  <a href="https://developers.facebook.com/tools/accesstoken/">
                    https://developers.facebook.com/tools/accesstoken/
                  </a>
                  . Note that using a token for a different app might change the
                  privacy groups you have access to.
                </Form.Text>
              </Form.Group>

              <Button
                variant="primary"
                onClick={_ => onSubmit(formik.values.token)}
                disabled={formik.values.token === '' || !!formik.errors.token}>
                Update
              </Button>
            </Form>
          </Card.Body>
        </Accordion.Collapse>
      </Accordion>
    </Card>
  );
}
