// Variables for the do_import_scheme import_wizard page

class ImportScheme {
    id;                     // ID from the database
    items = [];             // ImportSchemeItem objects
    base_url;               // Base URL for loading from the system
    accordion_container;    // ID of the DOM object being used to hold the accordion
    // _this = this;

    constructor(args){
        // Set up the ImportScheme and get its items
        this.id = args.id;
        this.base_url = args.base_url;
        this.accordion_container = args.accordion_container;

        this.get_items();
    };

    find_item_by_id(id){
        /// Get an item from the list by the database id
        return this.items.find(item => item.id == id);
    };

    find_item_by_model(model){
        /// Get an item from the list by model name
        return this.items.find(item => item.model == model);
    };

    get_items(){
        // Get a list of import_scheme_items from the backend
        $.ajax(this.base_url+'/list', {
            // pass this to caller so it's referrable inside the done function
            caller: this,
            dataType: 'json',
            cache: false,
        }).done(function(data){
            let items = data.import_scheme_items;
            
            for (let item in items){
                this.caller.items.push(new ImportSchemeItem({id: items[item], index: this.caller.items.length, parent: this.caller}))
                
                // Set up a base_accordion_X as a placeholder for the accordion block
    
                $(this.caller.accordion_container).append("<div id='base_accordion_" + (this.caller.items.length-1) + "'></div>");
            };
        });
    };
};

class ImportSchemeItem{
    id;                         // ID from the database or name.  Used for loading
    index;                      // Index number of the list of items from the parent
    name;                       // Name to be displayed in the accoridon button
    description;                // Description to be displayed in the accordion body - placeholder for HTML form or whatnot
    form;                       // The form to use to collect information about this item
    urgent = false;             // Is the Item urgent, meaning that it needs to be dealt with before the import can happen
    start_expanded;             // If true, the accordion will start in an expanded state
    dirty;                      // Indicates that the item is dirty and needs to be rerendered
    parent;                     // ImportScheme this Item belongs to
    selectpicker;               // If true, executes $('.selectpicker').selectpicker();
    tooltip;                    // If true, executes $('[data-toggle="tooltip"]').tooltip()
    fields = [];                // Holds a list of all the fields in this item
    model;                      // name of the model this item represents
    is_key_value_model;         // If true sets up script and objects to handle column_to_row
    key_value_model_fields = {};// A dict of the fields that will be used in the column_to_row
    key_value_model_setup = []; // A list of dicts, one per row, to set up the table
    key_value_model_keys = [];  // A list of the existing key values available to select for rows
    key_value_next_row = 0;     // Holds the ID for the next row

    // objects that corrispond with the dom objects for this item
    accordion;
    button;
    collapse;
    body;

    constructor(args){
        this.id = args.id;
        this.index = args.index;
        this.parent = args.parent;

        this.load();
    };

    load(args){
        // Load the ImportSchemeItem from the backend
        let load_url = this.parent.base_url+'/'+this.id;

        $.ajax(load_url, {
            // pass this to caller so it's referrable inside the success function
            caller: this,
            dataType: 'json',
            cache: false,
        }).done(function(data){
            this.caller.set_with_dirty({field: 'name', value: data.name});
            this.caller.set_with_dirty({field: 'description', value: data.description});
            this.caller.set_with_dirty({field: 'form', value: data.form});
            this.caller.set_with_dirty({field: 'urgent', value: data.urgent});
            this.caller.set_with_dirty({field: 'start_expanded', value: data.start_expanded});
            this.caller.set_with_dirty({field: 'selectpicker', value: data.selectpicker});
            this.caller.set_with_dirty({field: 'tooltip', value: data.tooltip});
            this.caller.set_with_dirty({field: 'model', value: data.model});
            this.caller.set_with_dirty({field: 'fields', value: data.fields});
            this.caller.set_with_dirty({field: 'is_key_value_model', value: data.is_key_value_model});
            this.caller.set_with_dirty({field: 'key_value_model_keys', value: data.key_value_model_keys});
            this.caller.set_with_dirty({field: 'key_value_model_setup', value: data.key_value_model_setup});
            
            this.caller.render();
        })
    };

    set_with_dirty(args){
        // Sets the field value if different from current, and if so sets dirty to true
        if ((Array.isArray(args.value) && ! arraysEqual(args.value, this[args.field])) || (! Array.isArray(args.value) && this[args.field] != args.value)){
            this[args.field] = args.value;
            this.dirty=true;
        }
    }

    render(args){
        // Create the structure of the accoridion

        // If the accordion item doesn't exist yet, create it
        if (! $('#accordion_'+this.id).length){
            // Replace base_accordion_X with the actual accordion from template
            $("#base_accordion_"+this.index).replaceWith(ITEM_TEMPLATE.replaceAll("!ACCORDION_ID!", this.id))

            // Assign the dom object refrences for this item
            this.accordion = $('#accordion_'+this.id)
            this.button = $('#button_'+this.id);
            this.collapse = $('#collapse_'+this.id);
            this.body = $('#body_'+this.id);
        };

        // If the item isn't dirty, no reason to render it
        if (! this.dirty){
            return 1;
        };
        
        this.button.html(this.name);

        let body_bit = "";
        if (this.description){body_bit += this.description}
        if (this.form){
            if (this.description){body_bit += "<br><br>"}
            body_bit += this.form
        }
        this.body.html(body_bit);

        // Set the propper css classes and open/close if item is urgent
        if (this.urgent){
            this.accordion.removeClass('border-primary');

            this.accordion.addClass('border-danger');
            this.button.addClass('accordion-urgent-button');
        } else {
            this.accordion.removeClass('border-danger');
            this.button.removeClass('accordion-urgent-button');

            this.accordion.addClass('border-primary');
        };

        // Open or close accordion based on start_expanded
        if (this.start_expanded){
            this.collapse.collapse('show');
        } else {
            this.collapse.collapse('hide');
        };
        
        if (this.selectpicker){
            $('.selectpicker').selectpicker();
        };

        if (this.tooltip){
            $('[data-toggle="tooltip"]').tooltip()
        };

        for (let row in this.key_value_model_setup) {
            this.create_key_value_row(this, this.key_value_model_setup[row].name, this.key_value_model_setup[row].id, this.key_value_model_setup[row].key)
        }
        
        if (this.form){
            // Attach funciton to move file fields into a key_value_model table
            var caller = this;

            $("#key_value_model_button_"+this.model).button().click(function(){
                caller.create_key_value_row(caller)
            });    

            // Attach ajax function to submit the form
            $("#item_form_"+this.model).submit(function (event) {
                event.preventDefault();

                let model = window.import_scheme.find_item_by_model($(this).attr("data-model"));

                let form_data = {
                    csrfmiddlewaretoken: getCookie('csrftoken'),
                };

                if ($(this).attr("data-file_saved")){
                    form_data["---file_saved---"] = $(this).attr("data-file_saved");
                };

                // Prepare if the model is a key_value model
                if (model.is_key_value_model){
                    form_data["**is_key_value_model**"] = true;

                    if ($("input[name='key_value_model_control_import_" + model.model + "']:checked").val() == "no_import"){
                        form_data["**no_import**"] = true;
                    }
                    else {
                        for (let row in model.key_value_model_fields){
                            let key = $("#key_value_model_table_key_" + model.model + "_" + row).find(":selected").val();
                            if (key == "**raw_text**"){
                                key = $("#key_value_model_table_key_" + model.model + "_" + row + "_raw_text").val()
                            }
                            
                            form_data[key] = model.key_value_model_fields[row];
                        }
                    }
                }

                // Prepare for standard models
                else{
                    for (let field_index in model.fields){
                        let field = model.fields[field_index];
                        
                        if($("#file_field_" + field).attr("data-is_radio")){
                            form_data[field] = $("#file_field_" + field + " input:radio:checked").val()
                        }
                        else if($("#file_field_" + field).attr("data-is_dropdown")){
                            form_data[field] = $("#file_field_" + field).find(":selected").val()
                        }
                        else{
                            let field_name = field.split("__-__").pop();
                        
                            form_data[field_name + ":file_field"] = $("#file_field_"+field).find(":selected").val();

                            form_data[field_name + ":file_field_raw_text"] = $("#file_field_" + field + "_raw_text").val();

                            form_data[field_name + ":file_field_first_1"] = $("#file_field_" + field + "_first_1").val();
                            form_data[field_name + ":file_field_first_2"] = $("#file_field_" + field + "_first_2").val();
                            form_data[field_name + ":file_field_first_3"] = $("#file_field_" + field + "_first_3").val();

                            form_data[field_name + ":file_field_split"] = $("#file_field_" + field + "_split").val();
                            form_data[field_name + ":file_field_split_splitter"] = $("#file_field_" + field + "_split_splitter").val();
                            form_data[field_name + ":file_field_split_position"] = $("#file_field_" + field + "_split_position").val();

                            // Get resolver attributes seperately because we don't know how many there will be at start
                            if(form_data[field_name + ":file_field"].startsWith("resolver:")){
            
                                let resolver = form_data[field_name + ":file_field"].split(":").pop();
                                let resolver_argument_base = `resolver_${field}__-__${resolver}__-__`;
                                let arg_list = $(`[id^=${resolver_argument_base}]`).map(function(){return this.id}).get();
                                
                                for(let argument_index in arg_list){
                                    let argument = arg_list[argument_index]
                                    let argument_name = argument.split("__-__").pop();

                                    form_data[`${field_name}:resolver:${resolver}:${argument_name}`] = $(`#${argument}`).find(":selected").val()
                                };
                            };
                        };
                    };
                };

                console.log(form_data);

                $.ajax({
                    type: "POST",
                    url: window.import_scheme.base_url + "/" +  $(this).attr("data-url"),
                    data: form_data,
                    // contentType: 'application/json',
                    dataType: "json",
                    encode: true,
                    caller: this,
                }).done(function (data) {
                    window.import_scheme.find_item_by_model($(this.caller).attr("data-model")).load();
                });

            });
        };

        // Set dirty to false so it won't rerender if it doesn't need to
        this.dirty = false;
        check_submittable(this.model);
    }

    check_submittable(){
        // Check to see if the form is good to be submitted
        // If it is set the submit button to enabled

        if (this.is_key_value_model){
            if ($("input[name='key_value_model_control_import_" + this.model + "']:checked").val() == "import"){

                if ($("[id^='key_value_model_table_key_" + this.model + "_']").length == 0){
                    return false;
                }

                // I will never understand why JS gives you indexes instead of values with a for .. in for a list
                let stupid_list = $("[id^='key_value_model_table_key_" + this.model + "_']").map(function(){return $(this).find(":selected").val()}).get();
                for (let key in stupid_list){
                    if (! stupid_list[key]){
                        return false;
                    }
                    if (stupid_list[key] == "**raw_text**"){
                        if(! $("#key_value_model_table_key_" + this.model + "_" + key + "_raw_text").val()){
                            return false;
                        }
                    }
                }
            }
        }
        else {
            for (let field_id in this.fields){
                let field_name = this.fields[field_id];
                let field_tag = "#file_field_" + field_name;
                let field = $(field_tag);
                let field_select_value = field.find(":selected").val();

                // Reject if field is blank
                if(field.attr("data-is_radio")){
                    if($(field_tag + " input:radio:checked").val() == undefined){
                        return false;
                    }
                }

                if(field.attr("data-is_dropdown")){
                    if(field_select_value == ""){
                        return false;
                    }
                }

                if(field_select_value == ""){
                    return false;
                };

                // Reject if field is "**raw_text**" and "raw_text" input is blank
                if(field_select_value == "**raw_text**"){
                    if ($(field_tag + "_raw_text").val() == ""){
                        return false;
                    };
                }; 

                // Reject if field is "**select_first**" and 'select_first' input is blank
                if(field_select_value == "**select_first**"){
                    let first_count = 0;
                    let first_values = [];

                    for (let count=1; count < 4; count++)
                    {
                        let value = $(field_tag + "_first_" + count).val();
                        if (value){
                            if (first_values.includes(value)){
                                return false;
                            };
                            first_values.push(value);
                            first_count ++;
                        };
                    };

                    if (first_count < 2){
                        return false;
                    };
                }; 

                // Reject if field is "**split_field**" and '_split_field', '_split_splitter', or '_split_position' input is blank
                if(field_select_value == "**split_field**"){
                    if (! $(field_tag + "_split").val() ||
                        ! $(field_tag + "_split_splitter").val() ||
                        ! $(field_tag + "_split_position").val()
                    ){
                        return false;
                    };
                }; 

                // Reject if field is a Resolver field and not all arguments are filled
                if(field_select_value && field_select_value.startsWith("resolver:")){

                    let resolver = field_select_value.split(":")[1];
                    let resolver_argument_base = `resolver_${field_name}__-__${resolver}__-__`;

                    // Build a list of values of resolver arguments and see if any of them are ""
                    if ($(`[id^=${resolver_argument_base}]`).map(function(){return this.value}).get().includes("")){
                        return false;
                    };
                };
            };
        };

        // Accept if we get to this point
        return true;
    }

    create_key_value_row(caller, initial_name, initial_id, initial_key){
        // Set up to feed from the dropdown if not given specific data
        let feeder = $("#key_value_model_feeder_" + caller.model).find(":selected");
        let field_name = "";
        let field_id = "";
        let raw_text = false;
        let selected = "";

        if (initial_name) {field_name = initial_name} else {field_name = feeder.attr("data-name")}''
        if (initial_id) {field_id = "**field**" + initial_id} else {field_id = feeder.val()};
        
        let table = document.getElementById("key_value_model_table_" + caller.model);
        let row_number = caller.key_value_next_row ++;

        caller.key_value_model_fields[row_number]=field_id;
        
        // Create a dropdown for the keys
        let key_fields = "<select id='key_value_model_table_key_" + caller.model + "_" + row_number + "' ";
        key_fields += "class='selectpicker border rounded-3' title='Key name...' ";
        key_fields += "onchange=\"manage_key_value_model_table('" + caller.model + "', '" + row_number + "')\" >";
        key_fields += "<option></option>";

        key_fields += "<optgroup label='Keys already in " + caller.name + "...'>";
        for (let key_index in caller.key_value_model_keys){
            let key = caller.key_value_model_keys[key_index];
            if (initial_key && key == initial_key) {selected = " selected"} else {selected = ""};

            key_fields += "<option value='" + key + "'" + selected + ">" + key + "</option>";
        }
        key_fields += "</optgroup>";

        key_fields += "<optgroup label='Raw text...'>";
        if (initial_key && field_name != initial_key && ! caller.key_value_model_keys.includes(initial_key)) {selected = " selected"} else {selected = ""};
        key_fields += "<option value='**raw_text**'" + selected + ">Enter Text</option>";
        key_fields += "</optgroup>";

        key_fields += "<optgroup label='File field name...'>";
        if (initial_key && field_name == initial_key) {selected = " selected"} else {selected = ""};
        key_fields += "<option value='" + field_name + "'" + selected + ">" + field_name + "</option>"
        key_fields += "</optgroup>";

        key_fields += "</select>";

        // Text field
        let text_value = "";
        let visibility = " not-visible";

        if (initial_key && field_name != initial_key && ! caller.key_value_model_keys.includes(initial_key)) {text_value = ' value="' + initial_key + '"'; visibility=""};
        key_fields += "<input type='text' placeholder='Specify key name ...' ";
        key_fields += "id='key_value_model_table_key_" + caller.model + "_" + row_number + "_raw_text' class='form-control" + visibility + "'";
        key_fields += "oninput=\"manage_key_value_model_table('" + caller.model + "', '" + row_number + "')\"" + text_value + ">";

        let row=table.insertRow();
        
        row.id = "key_value_model_table_row_" + caller.model + "_" + row_number;

        let cell1=row.insertCell();
        let cell2=row.insertCell();

        cell1.id = "key_value_model_table_field_" + caller.model + "_" + row_number;

        cell1.classList.add("align-middle");
        cell2.classList.add("align-middle");

        cell1.innerHTML="<a onclick=\"delete_key_value_model_row('" + caller.model + "', '" + row_number + "')\"> <img class='pointer' src='/static/ml_import_wizard/images/close.svg' height=25 width=25></a>"+field_name;
        cell2.innerHTML=key_fields;

        $('.selectpicker').selectpicker();
        check_submittable(caller.model);
        manage_key_value_model_feeder_input(caller.model)
    }
};


function check_submittable(model){
    /// Check to see if the form is good to be submitted

    if (window.import_scheme.find_item_by_model(model).check_submittable()) {
        $("#submit_" + model).removeClass('disabled');
    }
    else {
        $("#submit_" + model).addClass('disabled');
    };
}


function manage_key_value_model_control_import(model){
    /// Turn on and off key_value model inputs

    if ($("input[name='key_value_model_control_import_" + model + "']:checked").val() == "import"){
        $("#key_value_model_outer_" + model).removeClass("not-visible")
    }
    else {
        $("#key_value_model_outer_" + model).addClass("not-visible")
    }

    check_submittable(model);
}


function delete_key_value_model_row(model, row){
    /// Delete a row from the key_value_model_table

    $("#key_value_model_table_row_" + model + "_" + row).remove();

    // Remove the field from the list of fields
    delete(window.import_scheme.find_item_by_model(model).key_value_model_fields[row]);
    manage_key_value_model_feeder_input(model)
}


function manage_key_value_model_feeder_input(model){
    /// Check key_value_model_feeder to decide if the add button should be disabled

    let feeder = $("#key_value_model_feeder_" + model).find(":selected");
    if (feeder.val() && ! Object.values(window.import_scheme.find_item_by_model(model).key_value_model_fields).includes(feeder.val())) {
        $("#key_value_model_button_" + model).removeClass('disabled');
    }
    else {
        $("#key_value_model_button_" + model).addClass('disabled');
    }
}


function manage_key_value_model_table(model, row){
    if($("#key_value_model_table_key_" + model + "_" + row).find(":selected").val() == "**raw_text**"){
        $("#key_value_model_table_key_" + model + "_" + row + "_raw_text").removeClass('not-visible');
    }
    else {
        $("#key_value_model_table_key_" + model + "_" + row + "_raw_text").addClass('not-visible');
    }

    check_submittable(model)
}


function manage_file_field_input(field, model){
    /// Run when selects are updated to show or hide cascading fields
    /// Field contains model and field "model__-__field"

    let field_name = "#file_field_" + field;
    let field_raw_name = "file_field_" + field;
    let field_value = $(field_name).find(":selected").val();

    if(field_value == "**raw_text**"){
        $(field_name + "_raw_text").removeClass('not-visible');
    }
    else {
        $(field_name + "_raw_text").addClass('not-visible');
    };

    if(field_value == "**select_first**"){
        $(field_name + "_first_hider").removeClass('not-visible');
    }
    else {
        $(field_name + "_first_hider").addClass('not-visible');
    };

    if(field_value == "**split_field**"){
        $(field_name + "_split_hider").removeClass('not-visible');
    }
    else {
        $(field_name + "_split_hider").addClass('not-visible');
    };

    // Set all resolver: _hiders to not-visible to start with to limit duplication of code
    $("[id ^='resolver_" + field + "__-__'][id $='_hider']").addClass("not-visible")

    if(field_value.startsWith("resolver:")){
        let resolver = field_value.split(":")[1];
        $("#resolver_" + field + "__-__" + resolver + "_hider").removeClass("not-visible")
    };

    check_submittable(model);
};


function prep_upload_progress_bar(args){
    const file_fields = args.file_input_names
    const progress_bar = document.getElementById(args.progress_bar_name);
    const progress_modal = $('#'+args.progress_bar_name+'_modal_control');
    const progress_content = $('#'+args.progress_content);

    $("#"+args.form_name).bind( "submit", function(e) {
        e.preventDefault();
        var formData = new FormData(this);
        
        let file_names = "";
        for (let file_index in file_fields){
            let file = file_fields[file_index];
            file_field = document.getElementById(file).files[0];
            if (file_field != null){
                file_names += file_field.name + "<br>";
            }
        }
        
        progress_content.html(file_names + '<br>');
        progress_modal.modal('show');

        $.ajax({
            type: 'POST',
            url: args.post_url,
            data: formData,
            dataType: 'json',
            beforeSend: function(){
            },
            xhr:function(){
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', e=>{
                    if(e.lengthComputable){
                        const percentProgress = (e.loaded/e.total)*100;
                        progress_bar.innerHTML = `<div class="progress-bar progress-bar-striped bg-success" 
                role="progressbar" style="width: ${percentProgress}%" aria-valuenow="${percentProgress}" aria-valuemin="0" 
                aria-valuemax="100"></div>`
                    }
                });
                return xhr
            },
            success: function(response){
                progress_modal.modal('hide');
                window.import_scheme.find_item_by_id(0).load();
            },
            error: function(err){
                console.log(err);
            },
            cache: false,
            contentType: false,
            processData: false,
        });
    });
};


function getCookie(name) {
    /// Django's get cookie function from https://docs.djangoproject.com/en/4.1/howto/csrf/
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// Borrowed from https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
function arraysEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return false;
    if (a.length !== b.length) return false;
  
    // If you don't care about the order of the elements inside
    // the array, you should sort both arrays here.
    // Please note that calling sort on an array will modify that array.
    // you might want to clone your array first.
  
    for (var i = 0; i < a.length; ++i) {
      if (a[i] !== b[i]){
        consol.log("|" + a[i] + "| is different from |" + b[i] + "|");
        return false;
      }
    }
    return true;
  }