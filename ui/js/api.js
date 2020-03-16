// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
function set_searches() {
    /**
     * Set the search list in local storage.
     */
    var search_list = [];
    $('#search_list li').each(function(i, obj) {
        var d = {
            search_name: $(obj).attr('data-label'),
            search_type: $(obj).attr('data-type'),
            search_term: $(obj).attr('data-term'),
        }
        search_list.push(d);
    });
    window.localStorage.setItem("searches", JSON.stringify(search_list));
}

function set_token() {
    /**
     * Set the access token in local storage.
     */
    window.localStorage.setItem("token", access_token);
}

function get_searches() {
    /**
     * Get the search list out of local storage.
     */
    return JSON.parse(window.localStorage.getItem("searches"));
}

function get_token() {
    /**
     * Get the access token out of local storage.
     */
    return window.localStorage.getItem("token");
}

function htmlEntities(str) {
    /**
     * Replaces characters with their associated entity for safe use.
     * @param {string} str: The string to convert.
     */
    return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function display_error(message) {
    /**
     * Displays an error message in the UI that the user can dismiss.
     * @param {string} message: The message to display.
     */
    $("#error_notification").html(message + "<br /><br />")
    .css('color', 'red')
    .addClass("glyphicon")
    .addClass("glyphicon-remove");
}

function remove_error() {
    /**
     * Removes an error message in the UI that the user dismissed.
     */
    $("#error_notification").html('')
    .removeClass("glyphicon")
    .removeClass("glyphicon-remove");
}

function show_div(elem) {
    /**
     * The main div in the UI is the area that is not the top bar or the search
     * bar. Its contents is unique to a specific search list item. When clicking
     * on a list item, hide all of the divs except for the one with the content
     * related to the list item selected.
     * @param {string} elem: The id of the div to show.
     */
    $.each($('#main_content').children('div'), function() {
        if (!$(this).hasClass('sidebar')) {
            $(this).hide();
        }
    });
    $('#' + elem).show();
}

function clear_add_form() {
    /**
     * Clear the contents of the add form for re-use.
     */
    $('#add-new-object-form').find('input').each(function(i, obj) {
        $(obj).val('');
    });
    $('#add-new-object-form').find('textarea').val('');
}

function update_privacy_members(json) {
    /**
     * Update the privacy members in the Add/Edit form.
     * @param {Object} json: The data to update with.
     */
    elem = $('select#id_privacy_members');
    $.each(json.data, function(idx, member){
        var opt = $('<option name="' + member.id + '" value="' + member.id + '">' + member.name + '</option>');
        elem.append(opt);
    });
}

function get_members() {
    /**
     * GET request to acquire the Threat Exchange Members list. Once acquired,
     * format it and set the formatted HTML to be the contents of the popover.
     */
    $.ajax({
        type: "GET",
        url: threat_exchange_members + "?access_token=" + access_token,
        error: function (xhr, status) {
            $('#member-popover-content').text("Enter app-id and app-secret!");
        },
        success: function(json) {
            var html = $('<div></div>')
                .css('max-height', '500px')
                .css('overflow-y', 'auto');
            $.each(json.data, function(idx, member){
                var mailto = '<a href="mailto:' + member.email + '">' + member.name + '</a>';
                html.append(mailto + "<br />");
            });
            $('#member-popover-content').html(html);
            $('#member-popover').popover('show');
        },
    });
}

function refresh_search(search_type, search_term, div_id) {
    /**
     * Refresh the contents of a search. This is also used to add the initial
     * contents of the search since it's the same code.
     * @param {string} search_type: The type of search being performed.
     * @param {string} search_term: The search term provided in the search box.
     * @param {string} div_id: The div object.
     */
    var search_li = $('li[data-div=' + div_id + ']');
    var st = search_li.find('a:first-child');
    if (st.text().indexOf(')') > -1) {
        st.text(st.text().split(' ').slice(0, -1).join(' '));
    }
    if (search_type == 'threat_descriptors') {
        threat_descriptor_search(search_term, div_id);
    } else if (search_type == 'threat_indicators') {
        threat_indicator_search(search_term, div_id);
    } else if (search_type == 'malware') {
        malware_search(search_term, div_id);
    } else if (search_type == 'malware_families') {
        malware_family_search(search_term, div_id);
    } else if (search_type == 'url') {
        url_search(search_term, div_id);
    } else if (search_type == 'details') {
        search_term = detail_term(search_term);
        search_term = fbte_url + search_term;
        url_search(search_term, div_id);
    } else {
        display_error("Invalid Search Type");
    }
}

function add_search(search_name, search_type, search_term) {
    /**
     * Add a list item to the search list. Generate a unique div_id and set that
     * to a data attribute of the list item. This will be the id that will link
     * it to a main div later on. This also adds an animated loading icon to
     * give user feedback that something is happening.
     * @param {string} search_name: The name of this search.
     * @param {string} search_type: The type of search being performed.
     * @param {string} search_term: The search term provided in the search box.
     */
    var div_id = "div_id_" + search_counter;
    search_counter = search_counter + 1;
    var html = $('<li data-div="' + div_id + '"></li>')
               .attr('data-type', search_type)
               .attr('data-term', search_term)
               .attr('data-label', search_name);
    var link = $('<a href="#">' + search_name + '</a>')
               .css('display', 'inline-block')
               .attr('data-toggle', 'tooltip')
               .attr('data-original-title', search_term);
    var remove = $('<span></span>')
                 .attr('title', 'Remove search')
                 .addClass('glyphicon')
                 .addClass('glyphicon-remove')
                 .addClass('search_list_icon')
                 .addClass('remove_search');
    var loading = $('<span></span>')
                  .addClass('glyphicon')
                  .addClass('glyphicon-refresh')
                  .addClass('glyphicon-refresh-animate')
                  .addClass('search_refresh')
                  .addClass('search_list_icon')
                  .attr('title', 'Refresh');
    html.append(link);
    html.append(remove);
    html.append(loading);
    $('#search_list').append(html);
    refresh_search(search_type, search_term, div_id);
}

function display_results(elem, results) {
    /**
     * For each result in the 'data' list of the response, add a new list item
     * to the result list.
     * @param {Object} elem: The main div associated with these search results.
     * @param {string} results: The results from the response (JSON).
     */
    var html = $(elem).find('#result_list');
    if (typeof(results.data) == "undefined") {
        var tmp = results;
        var results = {
            data: [tmp]
        };
    }
    if (results.data.length < 1) {
        var d = $('<li>No results found!</li>');
        html.append(d);
    }
    $.each(results.data, function(idx, result) {
        if (typeof(result.indicator) != "undefined") {
            if (typeof(result.indicator.indicator) != "undefined") {
                var detail_val = result.indicator.indicator;
            } else if (typeof(result.indicator) != "undefined") {
                var detail_val = result.indicator;
            }
        } else if (typeof(result.md5) != "undefined") {
            var detail_val = result.md5;
        } else if (typeof(result.family_type) != "undefined") {
            var detail_val = result.family_type;
        }
        var d = $('<li></li>')
        var tlp = $('<span></span>')
                  .addClass('tlp')
                  .addClass('tlp_' + result.share_level);
        d.append(tlp);
        $.each(result, function(key, value) {
            //d.data('' + key, '' + value);
            d.attr('data-' + key, '' + value);
        });
        var permalink = $('<a href="' + fbte_url + result.id + '/"></a>')
                        .addClass('permalink')
                        .addClass('result_tall');
        permalink.append($('<span class="glyphicon glyphicon-link"></span>'));
        d.append(permalink);
        var data = $('<span>Added on: ' + result.added_on + '</span>')
                   .addClass('ellipsis');
        var detail_span = $('<span></span>')
                        .addClass('ellipsis')
                        .text(htmlEntities(detail_val));
        var content = $('<span></span>')
                      .css('width', '260')
                      .append(data)
                      .append(detail_span);
        d.append(content);
        html.append(d);
    });
    set_searches();
}

function remove_fetch(elem) {
    /**
     * Remove "Fetching more" list items.
     * @param {Object} elem: The element to remove list items from.
     */
    elem.find('.fetching_notification').remove();
}

function load_more(elem) {
    /**
     * Load more results if the pager is telling us there's more.
     * @param {Object} elem: The element to find next and to display results in.
     */
    var next = elem.attr('data-next');
    if (typeof(next) !== 'undefined'
        && elem.find('.fetching_notification').length < 1) {
        var fetching = $('<li>Fetching More...</li>')
                       .addClass('fetching_notification');
        var loading = $('<span></span>')
                      .addClass('glyphicon')
                      .addClass('glyphicon-refresh')
                      .addClass('glyphicon-refresh-animate');
        fetching.append(loading);
        elem.find('#result_list').append(fetching);
        $.ajax({
            type: "GET",
            url: next,
            error: function (xhr, status, thrown) {
                display_error(status + ": " + thrown);
            },
            success: function(json) {
                display_results(elem, json);
                remove_fetch(elem);
            },
        });
    }
}

function build_results(url, div_id, json) {
    /**
     * Build the main div for the search results. Add a search results section,
     * add a results list to the results section, add the details section,
     * remove the animated icon from the search list item and replace it with a
     * permalink icon (useful for sharing or copying the search URL).
     * @param {string} url: The URL used for this search.
     * @param {string} div_id: The ID to set for the main div.
     * @param {Object} json: The results from the response (JSON).
     */
    var parent = $('#main_content');
    var elem = $('<div id="' + div_id + '"></div>')
               .addClass('col-sm-9')
               .addClass('col-sm-offset-3')
               .addClass('col-md-10')
               .addClass('col-md-offset-2')
               .addClass('main');
    var search_results = $('<div></div>')
                         .addClass('col-sm-3')
                         .addClass('col-md-2')
                         .addClass('search_results')
                         .on('scroll', function(e) {
                            if ($(this)[0].scrollHeight - $(this).scrollTop() === $(this).outerHeight()) {
                                if (typeof($(this).attr('data-next') !== 'undefined')) {
                                    load_more($(this));
                                }
                            }
                         });
    var search_li = $('li[data-div=' + div_id + ']');
    var st = search_li.find('a:first-child');
    if (typeof(json.paging) !== 'undefined') {
        if (typeof(json.paging.next) !== 'undefined') {
            search_results.attr('data-next', json.paging.next);
            st.text(st.text() + ' (' + json.data.length + '+)');
        } else {
            st.text(st.text() + ' (' + json.data.length + ')');
        }
    }
    var result_list = $('<ul id="result_list"></ul>')
    search_results.append(result_list);
    elem.append(search_results);
    var item_details = $('<div></div>')
                       .addClass('col-sm-3')
                       .addClass('col-md-2')
                       .addClass('item_details');
    elem.append(item_details);
    search_li.attr('title', url);
    search_li.find('span.glyphicon-refresh').removeClass('glyphicon-refresh-animate');
    if (search_li.find('a.permalink').length < 1) {
        var permalink = $('<a href="' + url + '"></a>')
                        .addClass('permalink');
        var plicon = $('<span></span>')
                     .addClass('glyphicon')
                     .addClass('glyphicon-link');
        permalink.append(plicon);
        search_li.append(permalink);
    }
    parent.append(elem);
    show_div(div_id);
    display_results(elem, json);
}

function build_details(json, elem) {
    /**
     * Build the details div for a specific result list item.
     * @param {Object} json: The results from the response (JSON).
     * @param {Object} elem: The details div to add the content to.
     */
    var find_related = $('<div></div>').append($('<span class="related_label">Find Related</span>')
                   .css('float', 'left'));

    var related_options = $('<select class="related_options"></select>');
    if (typeof(json.indicator) !== "undefined") {
        related_options.append($('<option name="' + v_Connection.MALWARE_ANALYSES + '" value="' + v_Connection.MALWARE_ANALYSES + '">Malware Analyses</option>'));
        related_options.append($('<option name="' + v_Connection.RELATED + '" value="' + v_Connection.RELATED + '">Related</option>'));
    } else {
        related_options.append($('<option name="' + v_Connection.DROPPED + '" value="' + v_Connection.DROPPED + '">Dropped</option>'));
        related_options.append($('<option name="' + v_Connection.DROPPED_BY + '" value="' + v_Connection.DROPPED_BY + '">Dropped By</option>'));
        related_options.append($('<option name="' + v_Connection.FAMILIES + '" value="' + v_Connection.FAMILIES + '">Families</option>'));
        related_options.append($('<option name="' + v_Connection.THREAT_INDICATORS + '" value="' + v_Connection.THREAT_INDICATORS + '">Threat Indicators</option>'));
        related_options.append($('<option name="' + v_Connection.VARIANTS + '" value="' + v_Connection.VARIANTS + '">Variants</option>'));
    }
    find_related.append(related_options);
    find_related.append($('<button class="btn find_related" name="find_related">Go</button>'));

    var edit = $('<button class="btn edit_object" name="edit_object" id="edit_object">Edit Object</button>')
               .css('float', 'right');
    find_related.append(edit);

    var remove_related = $('<div></div>')
        .append($('<span class="remove_related_label">Remove Relation With</span>')
                .css('float', 'left'))
        .append($('<input class="remove_related_id" type="text" size="36" placeholder="ID" />'))
        .append($('<button class="btn remove_related" name="remove_related">Remove</button>'))
        .append($('<span id="remove_related_response"></span><br /><br />'));

    var related = $('<div></div>')
        .append($('<span class="relate_to_label">Relate To</span>')
                .css('float', 'left'))
        .append($('<input class="relate_to_id" type="text" size="36" placeholder="ID" />'))
        .append($('<button class="btn add_related" name="add_related">Relate</button>'))
        .append($('<span id="add_related_response"></span>'))
        .add($('<br />'));

    var html = $('<table></table>')
               .addClass('table')
               .addClass('details')
               .addClass('table-bordered')
               .addClass('table-striped');
    var th = $('<thead></thead>')
             .append($('<tr></tr>'))
             .append($('<th>Field</th><th>Value</th>'));
    html.append(th);
    var tb = $('<tbody></tbody>');
    $.each(json, function(key, value) {
        var tr = $('<tr></tr>');
        var td_key = $('<td></td>');
        var td_value = $('<td></td>');
        tr.attr('data-' + key, '' + JSON.stringify(value, null, 2));
        td_key.text(key);
        tr.append(td_key);
        if (key == 'sample') {
            var dl = $('<span></span>')
                     .addClass('glyphicon')
                     .addClass('glyphicon-download')
                     .addClass('sample_download');
            td_value.append(dl);
        } else {
            if (key == 'id') {
                related.attr('data-id', value);
                remove_related.attr('data-id', value);
                find_related.attr('data-id', value);
            }
            td_value.text(JSON.stringify(value, null, 2));
        }
        tr.append(td_value);
        tb.append(tr);
    });
    html.append(tb);
    var combined = find_related.add(html);
    combined = combined.add(related);
    combined = combined.add(remove_related);
    elem.html(combined);
}

function append_token(url) {
    /**
     * Depending on the URL, add the access_token parameter appropriately.
     * @param {string} url: The URL to append the access_token to.
     */
    if (url.slice(-1) == '/') {
        url = url + "?access_token=" + access_token;
    } else {
        url = url + "&access_token=" + access_token;
    }
    return url;
}

function details_request(url, elem) {
    /**
     * Send a GET request for details on a specific object.
     * @param {string} url: The URL for the details.
     * @param {Object} elem: The details div to add the results to.
     */
    $.ajax({
        type: "GET",
        url: append_token(url),
        error: function (xhr, status, thrown) {
            $('li[data-div=' + elem + ']').find('span.glyphicon-refresh').remove();
            display_error(status + ": " + thrown);
        },
        success: function(json) {
            build_details(json, elem);
        },
    });
}

function get_request(url, div_id) {
    /**
     * Send a GET request.
     * @param {string} url: The URL to send the search request to.
     * @param {string} div_id: The div_id associated with this search.
     */
    $.ajax({
        type: "GET",
        url: append_token(url),
        error: function (xhr, status, thrown) {
            $('li[data-div=' + div_id + ']').find('span.glyphicon-refresh').remove();
            display_error(status + ": " + thrown);
        },
        success: function(json) {
            build_results(url, div_id, json);
        },
    });
}

function show_results(elem, results) {
    /**
     * Show the results in the element provided.
     * @param {object} elem: The object to show the results in.
     * @param {object} results: The results of the request.
     */
    if (results.success) {
        var msg = " Success!";
    } else if (typeof(results.error) != "undefined") {
        var msg = results.error;
    }
    $(elem).text(msg);
}

function post_request(url, params, elem) {
    /**
     * Send a POST request.
     * @param {string} url: The URL to send the POST to.
     * @param {object} params: The data for the POST.
     * @param {object} elem: The element to add the results to.
     */
    var result = null;
    $.ajax({
        type: "POST",
        url: url + "?access_token=" + access_token,
        data: params,
        error: function (xhr, status, thrown) {
            display_error(status + ": " + thrown);
            result = {error: "An error has occurred."};
            show_results(elem, result);
        },
        success: function(json) {
            result = json;
            show_results(elem, result);
        },
    });
}

function delete_request(url, params, elem) {
    /**
     * Send a DELETE request.
     * @param {string} url: The URL to send the DELETE to.
     * @param {object} params: The data for the DELETE.
     * @param {object} elem: The element to add the results to.
     */
    var result = null;
    $.ajax({
        type: "DELETE",
        url: url + "?access_token=" + access_token,
        data: params,
        error: function (xhr, status, thrown) {
            display_error(status + ": " + thrown);
            result = {error: "An error has occurred."};
            show_results(elem, result);
        },
        success: function(json) {
            result = json;
            show_results(elem, result);
        },
    });
}

function parse_search_term(search_term) {
    /**
     * Parse search terms and generate URL paremeters for them.
     * @param {string} search_term: The search terms to use.
     */
    if (search_term.indexOf('text:') < 0
        && search_term.indexOf('strict_text:') < 0
        && search_term.indexOf('limit:') < 0
        && search_term.indexOf('since:') < 0
        && search_term.indexOf('until:') < 0
        && search_term.indexOf('type:') < 0
        && search_term.indexOf('threat_type:') < 0
        && search_term.indexOf('metadata:') < 0) {
            var new_term = "?text=" + search_term;
    } else {
        var new_term = search_term
                       .replace('strict_text:', '&strict_text=')
                       .replace('text:', '&text=')
                       .replace('limit:', '&limit=')
                       .replace('since:', '&since=')
                       .replace('until:', '&until=')
                       .replace('threat_type:', '&threat_type=')
                       .replace('type:', '&type=')
                       .replace('metadata:', '&metadata=')
                       .replace('&', '?')
    }
    return new_term;
}

function detail_term(detail_term) {
    /**
     * Parse detail terms and generate URL paremeters for them.
     * @param {string} detail_term: The detail terms to use.
     */

    terms = detail_term.split(" ");
    var new_term = "";
    var fields = "";
    var connection = "";
    $.each(terms, function(idx, value) {
        if (value.indexOf("fields") > -1) {
            fields = value.replace('fields:', '?fields=');
        } else if (value.indexOf("connection:") > -1) {
            var tmp = value.split(':')[1];
            connection = tmp + "/";
        } else {
            new_term = value + "/";
        }
    });
    new_term = new_term + connection + fields;
    return new_term;
}

function threat_descriptor_search(search_term, div_id) {
    /**
     * Search for Threat Descriptors.
     * @param {string} search_term: The search terms to use.
     * @param {string} div_id: The div_id associated with this search.
     */
    url_params = parse_search_term(search_term);
    url = threat_descriptors + url_params;
    var results = get_request(url, div_id);
}

function threat_indicator_search(search_term, div_id) {
    /**
     * Search for Threat Indicators.
     * @param {string} search_term: The search terms to use.
     * @param {string} div_id: The div_id associated with this search.
     */
    url_params = parse_search_term(search_term);
    url = threat_indicators + url_params;
    var results = get_request(url, div_id);
}

function malware_search(search_term, div_id) {
    /**
     * Search for Malware Analyses.
     * @param {string} search_term: The search terms to use.
     * @param {string} div_id: The div_id associated with this search.
     */
    url_params = parse_search_term(search_term);
    url = malware + url_params;
    var results = get_request(url, div_id);
}

function malware_family_search(search_term, div_id) {
    /**
     * Search for Malware Families.
     * @param {string} search_term: The search terms to use.
     * @param {string} div_id: The div_id associated with this search.
     */
    url_params = parse_search_term(search_term);
    url = malware_families + url_params;
    var results = get_request(url, div_id);
}

function url_search(url, div_id) {
    /**
     * Perform a search given an already-crafted URL.
     * @param {string} url: The URL to submit the GET request to.
     * @param {string} div_id: The div_id associated with this search.
     */
    var results = get_request(url, div_id);
}

function detail_search(list_elem, detail_id, elem) {
    /**
     * Get details on a specific object.
     * @param {Object} list_elem: The result list item clicked on.
     * @param {string} detail_id: The ThreatExchange object ID.
     * @param {Object} elem: The details div to add the results to.
     */
    var url = fbte_url + detail_id + "/";
    var results = details_request(url, elem);
}
