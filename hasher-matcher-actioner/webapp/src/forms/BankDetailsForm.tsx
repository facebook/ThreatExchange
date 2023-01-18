/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 */

import React, {useState, SyntheticEvent, useEffect} from 'react';
import {Form, Button} from 'react-bootstrap';
import {useFormik} from 'formik';

import PillBox from '../components/PillBox';

type BankDetailsValues = {
  bankName: string;
  bankDescription: string;
  isActive: boolean;
  tags: string[];
};

type BankDetailsFormProps = Partial<BankDetailsValues> & {
  handleSubmit: (
    bankName: string,
    bankDescription: string,
    isActive: boolean,
    tags: string[],
  ) => void;
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
  isActive,
  tags,
  handleSubmit,
  formResetCounter,
}: BankDetailsFormProps): JSX.Element {
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Change button state back to enabled when formResetCounter changes
    setSaving(false);
  }, [formResetCounter]);

  const formik = useFormik({
    initialValues: {
      bankName: bankName || '',
      bankDescription: bankDescription || '',
      isActive: isActive !== undefined && isActive,
      tags: tags === undefined ? [] : tags,
    },
    validate,
    onSubmit: values => {
      setSaving(true);
      handleSubmit(
        values.bankName,
        values.bankDescription,
        values.isActive,
        values.tags,
      );
    },
    enableReinitialize: formResetCounter !== undefined,
  });

  const innerHandleSubmit = (event: SyntheticEvent) => {
    event.preventDefault();
    formik.submitForm();
  };

  return (
    <Form className="hma-themed-form" onSubmit={innerHandleSubmit}>
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
        <Form.Label htmlFor="bankDescription">Bank Description</Form.Label>
        <Form.Text className="text-muted">
          Help others understand what this bank is for.
        </Form.Text>
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
      <Form.Group>
        <Form.Label>Matching</Form.Label>

        <Form.Switch
          id="isActive"
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          checked={formik.values.isActive}
          label="Match against members of this bank."
        />
      </Form.Group>

      <Form.Group>
        <Form.Label>Tags</Form.Label>
        <PillBox
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
      </Form.Group>
      <Button
        type="submit"
        variant="primary"
        disabled={saving || !formik.dirty}>
        Save
      </Button>
    </Form>
  );
}

BankDetailsForm.defaultProps = {
  formResetCounter: undefined,
};
