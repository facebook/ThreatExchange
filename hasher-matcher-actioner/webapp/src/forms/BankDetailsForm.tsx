/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, SyntheticEvent, useEffect} from 'react';
import {Form, Button} from 'react-bootstrap';
import {useFormik} from 'formik';

type BankDetailsValues = {
  bankName: string;
  bankDescription: string;
};

type BankDetailsFormProps = Partial<BankDetailsValues> & {
  handleSubmit: (bankName: string, bankDescription: string) => void;
  formResetCounter?: number;
};

function validate(values: BankDetailsValues) {
  const errors: Partial<BankDetailsValues> = {};
  if (!values.bankName) {
    errors.bankName = 'Required';
  }

  if (!values.bankDescription) {
    errors.bankDescription = 'Required';
  }

  return errors;
}

export default function BankDetailsForm({
  bankName,
  bankDescription,
  handleSubmit,
  formResetCounter,
}: BankDetailsFormProps) {
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Change button state back to enabled when formResetCounter changes
    setSaving(false);
  }, [formResetCounter]);

  const formik = useFormik({
    initialValues: {
      bankName: bankName || '',
      bankDescription: bankDescription || '',
    },
    validate,
    onSubmit: values => {
      setSaving(true);
      handleSubmit(values.bankName, values.bankDescription);
    },
    enableReinitialize: formResetCounter !== undefined,
  });

  const innerHandleSubmit = (event: SyntheticEvent) => {
    event.preventDefault();
    formik.submitForm();
  };

  return (
    <Form onSubmit={innerHandleSubmit}>
      <Form.Group className="mb-3 mt-4">
        <Form.Label htmlFor="bankName">Bank Name</Form.Label>
        <Form.Control
          id="bankName"
          type="text"
          placeholder=""
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          isValid={formik.touched.bankName && !formik.errors.bankName}
          isInvalid={formik.touched.bankName && !!formik.errors.bankName}
          value={formik.values.bankName}
        />
        {formik.touched.bankName && formik.errors.bankName ? (
          <Form.Control.Feedback type="invalid">
            {formik.errors.bankName}
          </Form.Control.Feedback>
        ) : null}
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label htmlFor="bankDescription">
          Bank Description. Help others understand what this bank is for.
        </Form.Label>
        <Form.Control
          id="bankDescription"
          as="textarea"
          rows={3}
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          isValid={
            formik.touched.bankDescription && !formik.errors.bankDescription
          }
          isInvalid={
            formik.touched.bankDescription && !!formik.errors.bankDescription
          }
          value={formik.values.bankDescription}
        />
        {formik.touched.bankDescription && formik.errors.bankDescription ? (
          <Form.Control.Feedback type="invalid">
            {formik.errors.bankDescription}
          </Form.Control.Feedback>
        ) : null}
      </Form.Group>
      <Button type="submit" variant="primary" disabled={saving}>
        Save
      </Button>
    </Form>
  );
}

BankDetailsForm.defaultProps = {
  formResetCounter: undefined,
};
