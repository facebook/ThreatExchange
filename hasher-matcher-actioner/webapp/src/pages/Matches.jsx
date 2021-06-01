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
import {SeparatorBorder} from '../utils/constants';

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
    <FullWidthLocalScrollingLeftAlignedLayout title="Matches">
      <Container className="h-100 v-100" fluid>
        {/* ^ This container is everything below the header */}
        <Row className="d-flex align-items-stretch h-100">
          {/* Each child of this row spans half the available space dividing into left and right pane. */}
          <Col
            md={6}
            className="d-flex flex-column justify-content-start h-100 px-0"
            style={{borderRight: SeparatorBorder}}>
            {/* This column is vertically split into the search bar and the table of search results. */}
            <div
              className="flex-grow-0 bg-light px-2"
              style={{borderBottom: SeparatorBorder}}>
              <MatchListFilters
                searchInAttribute={searchInAttribute}
                searchQuery={searchQuery}
              />
            </div>
            <div
              className="flex-grow-1 px-3"
              // Padding to align with search bar in match filters
              style={{overflowY: 'auto', overflowX: 'hidden'}}>
              <MatchList
                selection={selectedContentAndSignalIds}
                onSelect={setSelectedContentAndSignalIds}
                searchInAttribute={searchInAttribute}
                searchQuery={searchQuery}
              />
            </div>
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
    </FullWidthLocalScrollingLeftAlignedLayout>
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
    <Form className="mx-4" onSubmit={loadSearchPage}>
      <Form.Group className="mb-0">
        <Row className="my-2">
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
              ref={inputRef}
              onChange={e => setLocalSearchQuery(e.target.value)}
              value={localSearchQuery || ''}
            />
            <InputGroup.Append>
              <Button onClick={loadSearchPage}>Filter</Button>
            </InputGroup.Append>
          </InputGroup>
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
        <Row>
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
