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

export default function MatchIndex() {
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

  return (
    <Form>
      <Form.Group>
        <InputGroup>
          <InputGroup.Prepend>
            <Form.Control
              as="select"
              value={localSearchInAttribute}
              onChange={e => setLocalSearchInAttribute(e.target.value)}>
              <option value="contentId">Content ID</option>
              <option value="signalId">Signal ID</option>
            </Form.Control>
          </InputGroup.Prepend>
          <FormControl
            onChange={e => setLocalSearchQuery(e.target.value)}
            value={localSearchQuery || ''}
            htmlSize="40"
          />
          <InputGroup.Append>
            <Button onClick={loadSearchPage}>Search</Button>
          </InputGroup.Append>
        </InputGroup>
        <Form.Text>
          Search for matches of your content IDs or Signal IDs.
        </Form.Text>
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
        <div className="row mt-3">
          <div className="col-12">
            <table className="table table-hover small">
              <thead>
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
          </div>
        </div>
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
