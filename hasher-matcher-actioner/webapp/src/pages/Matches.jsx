/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import React, {useState, useEffect} from 'react';
import {useHistory} from 'react-router-dom';
import {PropTypes} from 'prop-types';
import {
  Container,
  Col,
  Button,
  Row,
  Collapse,
  InputGroup,
  Form,
  FormControl,
} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';
import classNames from 'classnames';

import {
  fetchAllMatches,
  fetchMatchesFromContent,
  fetchMatchesFromSignal,
} from '../Api';
import {timeAgo} from '../utils/DateTimeUtils';
import ContentMatchPane from '../components/ContentMatchPane';
import {useQuery} from '../utils/QueryParams';
import FullWidthLocalScrollingLeftAlignedLayout from './layouts/FullWidthLocalScrollingLeftAlignedLayout';
import '../styles/_matches.scss';

export default function Matches() {
  const query = useQuery();
  const filterString = query.get('contentId') || query.get('signalId');
  let filterAttribute;

  ['contentId', 'signalId'].forEach(attribute => {
    if (query.has(attribute)) {
      filterAttribute = attribute;
    }
  });

  const [
    selectedContentAndSignalIds,
    setSelectedContentAndSignalIds,
  ] = useState({
    contentId: undefined,
    signalId: undefined,
    signalSource: undefined,
  });

  return (
    <FullWidthLocalScrollingLeftAlignedLayout title="Matches">
      <Container className="h-100 v-100" fluid>
        {/* ^ This container is everything below the header */}
        <Row className="d-flex align-items-stretch h-100">
          {/* Each child of this row spans half the available space dividing into left and right pane. */}
          <Col
            md={6}
            className="left-pane d-flex flex-column justify-content-start h-100 px-0">
            {/* This column is vertically split into the filter input box and the table of filtered results. */}
            <div className="match-filter-box flex-grow-0 bg-light px-2">
              <MatchListFilters
                filterAttribute={filterAttribute}
                filterString={filterString}
              />
            </div>
            <div
              className="flex-grow-1 px-3"
              // Padding to align with input box in match filters
              style={{overflowY: 'auto', overflowX: 'hidden'}}>
              <MatchList
                selection={selectedContentAndSignalIds}
                onSelect={setSelectedContentAndSignalIds}
                filterAttribute={filterAttribute}
                filterString={filterString}
              />
            </div>
          </Col>
          <Col md={6}>
            {(selectedContentAndSignalIds.contentId === undefined && (
              <EmptyContentMatchPane />
            )) || (
              <ContentMatchPane
                contentId={selectedContentAndSignalIds.contentId}
                signalId={selectedContentAndSignalIds.signalId}
                signalSource={selectedContentAndSignalIds.signalSource}
              />
            )}
          </Col>
        </Row>
      </Container>
    </FullWidthLocalScrollingLeftAlignedLayout>
  );
}

function EmptyContentMatchPane() {
  return (
    <div className="h-100" style={{textAlign: 'center', paddingTop: '40%'}}>
      <h1 className="display-4 text-secondary">Nothing Selected!</h1>
      <p className="lead">
        Select a match on the left pane to see its details.
      </p>
    </div>
  );
}

/**
 * A box of filters for the list of matches that appear on the match filters page.
 */
function MatchListFilters({filterAttribute, filterString}) {
  const [localFilterAttribute, setLocalFilterAttribute] = useState(
    filterAttribute,
  );
  const [localFilterString, setLocalFilterString] = useState(filterString);

  useEffect(() => {
    /** Update state when props changed. */
    setLocalFilterAttribute(filterAttribute);
    setLocalFilterString(filterString);
  }, [filterAttribute, filterString]);

  const history = useHistory();
  const loadResults = e => {
    history.push(`?${localFilterAttribute}=${localFilterString}`);
    e.preventDefault(); // Prevent form submit
  };

  const inputRef = React.createRef();

  return (
    <Form className="mx-4" onSubmit={loadResults}>
      <Form.Group className="mb-0">
        <Row className="my-2">
          <InputGroup>
            <InputGroup.Prepend>
              <Form.Control
                as="select"
                value={localFilterAttribute}
                onChange={e => setLocalFilterAttribute(e.target.value)}>
                <option value="contentId">Content ID</option>
                <option value="signalId">Signal ID</option>
              </Form.Control>
            </InputGroup.Prepend>
            <FormControl
              ref={inputRef}
              onChange={e => setLocalFilterString(e.target.value)}
              value={localFilterString || ''}
            />
            <InputGroup.Append>
              <Button onClick={loadResults}>Filter</Button>
            </InputGroup.Append>
          </InputGroup>
        </Row>
      </Form.Group>
    </Form>
  );
}

MatchListFilters.propTypes = {
  filterAttribute: PropTypes.oneOf(['contentId', 'signalId']),
  filterString: PropTypes.string,
};

MatchListFilters.defaultProps = {
  filterAttribute: 'contentId',
  filterString: undefined,
};

function MatchList({selection, onSelect, filterAttribute, filterString}) {
  const [matchesData, setMatchesData] = useState(null);

  useEffect(() => {
    let apiPromise;
    if (filterAttribute === 'contentId') {
      apiPromise = fetchMatchesFromContent(filterString);
    } else if (filterAttribute === 'signalId') {
      /** Hack alert. This expects strings like
       * "facebook/threatexchange|12312121" to be the filterString. A pipe
       * separates the source from the signal id */
      const parts = filterString.split('|');
      apiPromise = fetchMatchesFromSignal(parts[0], parts[1]);
    } else {
      apiPromise = fetchAllMatches();
    }

    apiPromise.then(matches => setMatchesData(matches.match_summaries));
    // .catch(err => console.log(err));
  }, [filterAttribute, filterString]);

  return (
    <>
      <Spinner hidden={matchesData !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={matchesData !== null}>
        <Row>
          <Col>
            <table className="table table-hover small">
              <thead>
                {/* TODO: Undecided nomenclature */}
                <tr>
                  <th>Content Id</th>
                  <th>Matched in Dataset</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {matchesData !== null && matchesData.length ? (
                  matchesData.map(match => (
                    <tr
                      className={classNames('align-middle', {
                        'table-info':
                          match.content_id === selection.contentId &&
                          match.signal_id === selection.signalId,
                      })}
                      onClick={e =>
                        onSelect({
                          contentId: match.content_id,
                          signalId: match.signal_id,
                          signalSource: match.signal_source,
                          [e.target.name]: e.target.value,
                        })
                      }
                      key={`${match.signal_source}_${match.signal_id}_${match.content_id}`}>
                      <td className="align-middle">{match.content_id}</td>
                      <td className="align-middle">{match.signal_source}</td>
                      {/* <td className="align-middle">{match.signal_id}</td> */}
                      <td className="align-middle">
                        {timeAgo(match.updated_at)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>No Matches Found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </Col>
        </Row>
      </Collapse>
    </>
  );
}

MatchList.propTypes = {
  selection: PropTypes.shape({
    contentId: PropTypes.string,
    signalId: PropTypes.string,
  }),
  onSelect: PropTypes.func.isRequired,

  // Filter matches list
  filterAttribute: PropTypes.oneOf(['contentId', 'signalId']),
  filterString: PropTypes.string,
};

MatchList.defaultProps = {
  selection: {contentId: undefined, signalId: undefined},
  filterAttribute: 'contentId',
  filterString: undefined,
};
