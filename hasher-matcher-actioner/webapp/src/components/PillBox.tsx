/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, KeyboardEvent, FormEvent} from 'react';
import {Button, Form, InputGroup} from 'react-bootstrap';

import {IonIcon} from '@ionic/react';
import {close} from 'ionicons/icons';

import '../styles/_pill-box.scss';

type PillBoxProps = {
  pills: string[];
  handleNewTagAdd: (tag: string) => void;
  handleTagDelete: (tag: string) => void;
};

type PillProps = {
  tag: string;
  onDelete: () => void;
};

function Pill({tag, onDelete}: PillProps) {
  return (
    <span className="pill">
      <div className="pill-internal">
        <span className="expand has-label">{tag}</span>
        <span className="fixed">
          <Button onClick={onDelete} size="sm" variant="secondary">
            <IonIcon icon={close} />
          </Button>
        </span>
      </div>
    </span>
  );
}

/**
 * Provides an editable box of pills. One can add pills and remove pills. Adding
 * pills happens by an input.
 */
export default function PillBox({
  pills,
  handleNewTagAdd,
  handleTagDelete,
}: PillBoxProps) {
  const [newTagValue, setNewTagValue] = useState<string>('');

  const handleNewTagAddInner = () => {
    if (newTagValue !== '') {
      handleNewTagAdd(newTagValue);
    }

    setNewTagValue('');
  };

  return (
    <div>
      {pills.map(pill => (
        <Pill tag={pill} onDelete={() => handleTagDelete(pill)} />
      ))}
      <InputGroup size="sm">
        <Form.Control
          type="text"
          value={newTagValue}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setNewTagValue(e.target.value)
          }
          onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
            if (e.keyCode === 13) {
              e.stopPropagation();
              e.preventDefault();
              handleNewTagAddInner();
            }
          }}
          placeholder="Add new tag"
        />
        <InputGroup.Append>
          <Button onClick={handleNewTagAddInner} variant="secondary">
            Add
          </Button>
        </InputGroup.Append>
      </InputGroup>
    </div>
  );
}
