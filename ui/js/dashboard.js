// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
function check_token() {
    /**
     * Keeps track of the global access_token variable. Present the user with
     * an indication in the UI as to whether the variable is set to something or
     * not. We can't say for sure what is actually valid so the condition is
     * that there must be a string of some length greater than 0 on both sides
     * of the pipe.
     */
    at = access_token.split('|');
    if (at[0].length < 1 || at[1].length < 1) {
        $('#token_state').removeClass('glyphicon-thumbs-up')
        .addClass('glyphicon-thumbs-down')
        .css('color', '#FE2E2E')
        .attr('title', 'you need to set your app-id and app-secret!');
    } else {
        $('#token_state').removeClass('glyphicon-thumbs-down')
        .addClass('glyphicon-thumbs-up')
        .css('color', '#58FA82')
        .attr('title', 'app-id and app-secret already set!');
        set_token();
    }
}

$(document).ready(function() {
    // Check the access token when the page loads.
    check_token();

    var searches = get_searches();
    if (searches !== null) {
        $.each(searches, function(idx, obj) {
            add_search(obj.search_name, obj.search_type, obj.search_term);
        });
    }

    // Popover for when the user clicks on the "Query Help" link.
    var query_popover = $("#query_help").popover({
        placement : 'bottom',
        html: 'true',
        container: 'body',
        content: function(e) {
            return $('#query-popover-content').html();
        }
    });

    // Popover for when the user clicks on the "Members" link.
    var member_popover = $("#member-popover").popover({
        placement : 'bottom',
        trigger: 'manual',
        html: 'true',
        container: 'body',
        content: function(e) {
            return $('#member-popover-content').html();
        }
    }).on('click', function(e) {
        get_members();
    });

    // Popover for when the user clicks on the "ID & Secret" link.
    var ids_popover = $("#ids-popover").popover({
        placement : 'bottom',
        html: 'true',
        container: 'body',
        content: function() {
            return $('#ids-popover-content').html();
        }
    });

    // Close a popover when clicking outside of it, but not inside of it.
    $(document).on('click', function (e) {
        if ($(e.target).data('toggle') !== 'popover'
           && $(e.target).closest('div.popover-content').length < 1) {
            $.each($('[data-toggle="popover"]'), function(idx, elem) {
                if (typeof($(this).attr('aria-describedby')) !== "undefined") {
                    $(elem).popover('hide');
                }
            });
        }
    });

    // Make the modal draggable
    $('body').tooltip({
        selector: '[data-toggle=tooltip]',
        placement: top,
    });

    // Make the search sortable
    $('.sortable').sortable().bind('sortupdate', function(e, ui) {
        set_searches();
    });

    // Remove the error if the user has attempted to dismiss it.
    $("#error_notification").on('click', function(e) {
        remove_error();
    })

    // After selecting a search type, refocus to the search box.
    $("#search_type").on('change', function(e) {
        $('#api_search').focus();
    });

    // Perform a search given the selected type and contents of the search box.
    $('#api_search').keypress(function(event){
        var keycode = (event.keyCode ? event.keyCode : event.which);
        if(keycode == '13'){
            var search_name = $('#search_type option:selected').text();
            var search_type = $('#search_type option:selected').val();
            var search_term = $(this).val();
            add_search(search_name, search_type, search_term);
            $('#search_list li').last().children('a').click();
        }
    });

    // Actively manipulate the access_token global as a user enters an app-id.
    $(document).on('change paste keyup', 'input.app_id', function(e) {
        app_id = $(this).val();
        tmp = access_token.split("|");
        if (tmp.length <= 1) {
            access_token = $(this).val() + "|";
        }
        else if (tmp.length > 1) {
            access_token = $(this).val() + "|" + tmp[1];
        }
        check_token();
    });

    // Actively manipulate the access_token global as a user enters an app-secret.
    $(document).on('change paste keyup', 'input.app_secret', function(e) {
        app_secret = $(this).val();
        tmp = access_token.split("|");
        if (tmp.length <= 1) {
            access_token = "|" + $(this).val();
        }
        else if (tmp.length > 1) {
            access_token = tmp[0] + "|" + $(this).val();
        }
        check_token();
    });


    // Clear the search list.
    $('.clear_searches').on('click', function(e) {
        $.each($('#search_list li'), function() {
            var div_id = $(this).attr('data-div');
            $('#' + div_id).remove();
            $(this).remove();
        });
        set_searches();
    });

    // Select a search item and display the main div for it.
    $(document).on('click', '#search_list li a', function(e) {
        $.each($('#search_list li'), function() {
            $(this).removeClass("active");
        });
        $(this).parent().addClass("active");
        var elem = $(this).parent().attr('data-div');
        show_div(elem);
    });

    // Select a result item and submit a request for details on that object.
    $(document).on('click', '#result_list li', function(e) {
        if (highlighted_result != null) {
            highlighted_result.removeClass('active');
        }
        $(this).addClass('active');
        highlighted_result = $(this);
        var detail_id = $(this).data('id');
        if (typeof(detail_id) != "undefined") {
            var elem = $(this).parent().parent().next();
            detail_search($(this), detail_id, elem);
        }
    });

    // Remove a search
    $(document).on('click', 'span.remove_search', function(e) {
        var div_id = $(this).parent().attr('data-div');
        $('#' + div_id).remove();
        $(this).parent().remove();
        set_searches();
    });

    // Download a sample.
    $(document).on('click', '.sample_download', function(e) {
        var elem = $(this).parent().parent()
        var data = elem.attr('data-sample');
        var md5 = elem.parent().find('tr[data-md5]').attr('data-md5');
        var hiddenElement = document.createElement('a');

        /**
         * The data is b64encoded. Decoding it using atob() converts it into a
         * UTF-8 multi-byte representation. After b64decoding, build a
         * byte-array so we can send along the binary data (a zip file).
         */
        var contentType = "application/zip";
        var binary = atob(data)
        var array = new Uint8Array(binary.length)
        for( var i = 0; i < binary.length; i++ ) {
            array[i] = binary.charCodeAt(i);
        }
        var file = new Blob([array])
        hiddenElement.href = window.URL.createObjectURL(file);
        hiddenElement.target = '_blank';
        hiddenElement.download = md5 + '.zip';
        hiddenElement.click();
    });

    // When the modal opens, setup options and focus.
    $('#add-new-modal').on('shown.bs.modal', function(e) {

        $('#add-new-modal-edit').hide();
        $('#add-new-modal-submit').show();

        // Build Privacy Type
        var pt = $('select#id_privacy_type');
        if (pt.children('option').length < 1) {
            $.each(v_PrivacyType, function(k, v) {
                var opt = $('<option name="' + v + '">' + v + '</option>');
                pt.append(opt);
            });
        }

        // Build Privacy Members
        var pt = $('select#id_privacy_members');
        if (pt.children('option').length < 1) {
            $.ajax({
                type: "GET",
                url: threat_exchange_members + "?access_token=" + access_token,
                error: function (xhr, status) {
                    display_error("Bad connection or bad/no app-id/app-secret!");
                },
                success: function(json) {
                    update_privacy_members(json);
                },
            });
        }

        // Build Severity
        var pt = $('select#id_severity');
        if (pt.children('option').length < 1) {
            $.each(v_Severity, function(k, v) {
                var opt = $('<option name="' + v + '">' + v + '</option>');
                pt.append(opt);
            });
        }

        // Build Share Level
        var pt = $('select#id_share_level');
        if (pt.children('option').length < 1) {
            $.each(v_ShareLevel, function(k, v) {
                var opt = $('<option name="' + v + '">' + v + '</option>');
                pt.append(opt);
            });
        }

        // Build Status
        var pt = $('select#id_status');
        if (pt.children('option').length < 1) {
            $.each(v_Status, function(k, v) {
                var opt = $('<option name="' + v + '">' + v + '</option>');
                pt.append(opt);
            });
        }

        // Build Threat Type
        var pt = $('select#id_threat_type');
        if (pt.children('option').length < 1) {
            $.each(v_ThreatType, function(k, v) {
                var opt = $('<option name="' + v + '">' + v + '</option>');
                pt.append(opt);
            });
        }

        // Build Type
        var pt = $('select#id_type');
        if (pt.children('option').length < 1) {
            $.each(v_Types, function(k, v) {
                var opt = $('<option name="' + v + '">' + v + '</option>');
                pt.append(opt);
            });
        }

        $('#add-new-object-form [data-field]')[0].focus();
    });

    // Inject values into the "Add/Edit" form and enable Edit mode.
    $(document).on('click', '#edit_object', function(e) {
        $('#add-new-modal').modal();
        $('#add-new-modal-submit').hide();
        $('#add-new-modal-edit').show()
        .attr('data-id', $(this).parent().attr('data-id'));
        clear_add_form();
        var tbl = $(this).parent().parent().find('table');
        $(tbl).find('tr').each(function(i, obj) {
            var key = $(obj).find('td:first').text();
            var val = $(obj).find('td:last').text();
            // On GET we have 'threat_types' but on POST they require 'threat_type'...
            if (key == 'threat_types') {
                key = 'threat_type';
            }
            // The type comes back lowercase even though we need to submit uppercase...
            if (key == 'type') {
                val = val.toUpperCase();
            }
            $('#add-new-object-form').find("#id_" + key).val(val);
        });
    });

    // Submit the edit.
    $('#add-new-modal-edit').click(function(e) {
        if ($('#id_indicator').val()==="") {
            // invalid
            $('#id_indicator').next('.help-inline').show();
            return false;
        }
        else {
            // submit the form here
            var data = {};
            $('#add-new-object-form [data-field]').each(function(i, obj) {
                var field = $(obj).attr('data-field');
                var value = $(obj).val();
                if (!!value && value.length > 0) {
                    data[field] = value;
                }
            });
            var res_obj = $('span#add-new-object-results');
            if ("privacy_type" in data) {
                var url = fbte_url + $(this).attr('data-id') + "/"
                post_request(url, data, res_obj);
            } else {
                res_obj.text("Must have a privacy type!");
            }
            return false;
        }
    });

    // Submit the add.
    $('#add-new-modal-submit').click(function(e) {
        if ($('#id_indicator').val()==="") {
            // invalid
            $('#id_indicator').next('.help-inline').show();
            return false;
        }
        else {
            // submit the form here
            var data = {};
            $('#add-new-object-form [data-field]').each(function(i, obj) {
                var field = $(obj).attr('data-field');
                var value = $(obj).val();
                if (!!value && value.length > 0) {
                    data[field] = value;
                }
            });
            var res_obj = $('span#add-new-object-results');
            if ("privacy_type" in data) {
                var url = threat_descriptors;
                post_request(url, data, res_obj);
            } else {
                res_obj.text("Must have a privacy type!");
            }
            return false;
        }
    });

    // Add a related object.
    $(document).on('click', '.add_related', function(e) {
        var parent = $(this).parent()
        var id = parent.attr('data-id');
        var url = fbte_url + id + '/related/';
        var rel_id = parent.find('input').val();
        var data = {related_id: rel_id};
        post_request(url, data, $(this).next());
        return false;
    });

    // Remove a related object.
    $(document).on('click', '.remove_related', function(e) {
        var parent = $(this).parent()
        var id = parent.attr('data-id');
        var url = fbte_url + id + '/related/';
        var rel_id = parent.find('input').val();
        var data = {related_id: rel_id};
        delete_request(url, data, $(this).next());
        return false;
    });

    // Add a new search which are all of the related objects.
    $(document).on('click', '.find_related', function(e) {
        var parent = $(this).parent()
        var id = parent.attr('data-id');
        var related = $(this).prev().val();
        var url = fbte_url + id + '/' + related + '/';
        add_search('Find Related', 'url', url);
        $('#search_list li').last().children('a').click();
    });

    // Clear the little "Success" or "error" message next to this buton.
    $(document).on('click', '#add_related_response', function(e) {
        $(this).text('');
    });

    // Clear the little "Success" or "error" message next to this buton.
    $(document).on('click', '#remove_related_response', function(e) {
        $(this).text('');
    });

    // Refresh a search
    $(document).on('click', '.search_refresh', function(e) {
        $(this).addClass('glyphicon-refresh-animate');
        var parent = $(this).parent();
        var search_type = parent.attr('data-type');
        var search_term = parent.attr('data-term');
        var div_id = parent.attr('data-div');
        $('div#' + div_id).remove();
        refresh_search(search_type, search_term, div_id);
    });

    $(".modal-draggable .modal-dialog").draggable({
        handle: ".modal-header"
    });

});
