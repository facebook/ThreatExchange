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

export default function Matches() {
  const query = useQuery();
  const searchQuery = query.get('contentId') || query.get('signalId');
  let searchInAttribute;

  ['contentId', 'signalId'].forEach(attribute => {
    if (query.has(attribute)) {
      searchInAttribute = attribute;
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
    <div className="d-flex flex-column justify-content-start align-items-stretch h-100 w-100">
      <div className="flex-grow-0">
        <Container className="bg-dark text-light" fluid>
          <Row className="d-flex flex-row justify-content-between align-items-end">
            <div className="px-4 py-2">
              <h1>Matches</h1>
              <p>View content that has been flagged by the HMA system.</p>
            </div>
            <div className="px-4 py-2">
              <MatchListFilters
                searchInAttribute={searchInAttribute}
                searchQuery={searchQuery}
              />
            </div>
          </Row>
        </Container>
      </div>
      <div className="flex-grow-1" style={{overflowY: 'hidden'}}>
        <Container className="h-100 v-100" fluid>
          <Row className="d-flex align-items-stretch h-100">
            <Col className="h-100" style={{overflowY: 'auto'}} md={6}>
              <MatchList
                selection={selectedContentAndSignalIds}
                onSelect={setSelectedContentAndSignalIds}
                searchInAttribute={searchInAttribute}
                searchQuery={searchQuery}
              />
            </Col>
            <Col md={6}>
              {(selectedContentAndSignalIds.contentId === undefined && (
                <p>Select a match to see its details.</p>
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
      </div>
    </div>
  );
}

/**
 * A box of filters for the list of matches that appear on the match filters page.
 */
function MatchListFilters({searchInAttribute, searchQuery}) {
  const [localSearchInAttribute, setLocalSearchInAttribute] = useState(
    searchInAttribute,
  );
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery);

  useEffect(() => {
    /** Update state when props changed. */
    setLocalSearchInAttribute(searchInAttribute);
    setLocalSearchQuery(searchQuery);
  }, [searchInAttribute, searchQuery]);

  const history = useHistory();
  const loadSearchPage = e => {
    history.push(`?${localSearchInAttribute}=${localSearchQuery}`);
    e.preventDefault(); // Prevent form submit
  };

  const inputRef = React.createRef();

  return (
    <Form onSubmit={loadSearchPage}>
      <Form.Group>
        <Row className="mt-1">
          <InputGroup>
            <FormControl
              ref={inputRef}
              onChange={e => setLocalSearchQuery(e.target.value)}
              value={localSearchQuery || ''}
              htmlSize="40"
            />
            <InputGroup.Append>
              <Button onClick={loadSearchPage}>Search</Button>
            </InputGroup.Append>
          </InputGroup>
        </Row>
        <Row className="justify-content-between mt-3">
          <Col md="5">
            <Form.Check
              id="match-list-filter-radio-contentid"
              type="radio"
              value="contentId"
              label="Content ID"
              checked={localSearchInAttribute === 'contentId'}
              onChange={e => setLocalSearchInAttribute(e.target.value)}
            />
          </Col>
          <Col md="4">
            <Form.Check
              id="match-list-filter-radio-signalid"
              type="radio"
              value="signalId"
              label="Signal ID"
              checked={localSearchInAttribute === 'signalId'}
              onChange={e => setLocalSearchInAttribute(e.target.value)}
            />
          </Col>
          <Col md="3" className="push-right">
            <Button
              variant="light"
              size="sm"
              onClick={() => {
                setLocalSearchQuery('');
                inputRef.current.focus();
              }}>
              Clear
            </Button>
          </Col>
        </Row>
      </Form.Group>
    </Form>
  );
}

MatchListFilters.propTypes = {
  searchInAttribute: PropTypes.oneOf(['contentId', 'signalId']),
  searchQuery: PropTypes.string,
};

MatchListFilters.defaultProps = {
  searchInAttribute: 'contentId',
  searchQuery: undefined,
};

function MatchList({selection, onSelect, searchInAttribute, searchQuery}) {
  const [matchesData, setMatchesData] = useState(null);

  useEffect(() => {
    let apiPromise;
    if (searchInAttribute === 'contentId') {
      apiPromise = fetchMatchesFromContent(searchQuery);
    } else if (searchInAttribute === 'signalId') {
      /** Hack alert. This expects strings like
       * "facebook/threatexchange|12312121" to be the searchQuery. A pipe
       * separates the source from the signal id */
      const parts = searchQuery.split('|');
      apiPromise = fetchMatchesFromSignal(parts[0], parts[1]);
    } else {
      apiPromise = fetchAllMatches();
    }

    apiPromise.then(matches => setMatchesData(matches.match_summaries));
    // .catch(err => console.log(err));
  }, [searchInAttribute, searchQuery]);

  return (
    <>
      <Spinner hidden={matchesData !== null} animation="border" role="status">
        <span className="sr-only">Loading...</span>
      </Spinner>
      <Collapse in={matchesData !== null}>
        <Row className="mt-3">
          <Col>
            <table className="table table-hover small">
              <thead>
                {/* TODO: Undecided nomenclature */}
                <tr>
                  <th>Content Id</th>
                  <th>Matched in Dataset</th>
                  <th>Seen</th>
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
  searchInAttribute: PropTypes.oneOf(['contentId', 'signalId']),
  searchQuery: PropTypes.string,
};

MatchList.defaultProps = {
  selection: {contentId: undefined, signalId: undefined},
  searchInAttribute: 'contentId',
  searchQuery: undefined,
};
