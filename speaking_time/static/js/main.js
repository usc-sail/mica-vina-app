var serial_num = new Object();
// AJAX polling to get progress update every 1 second 
function getStatus(taskID) {
  $.ajax({
    url: `/tasks/${taskID}`,
    method: 'GET'
  })
  .done((res) => {
   //var s_num = document.getElementById("taskTable").rows.length-3;
    if (parseInt(document.getElementById("taskTable").rows.length) == 3) s_num = 0; //Hack to initialize table serial number in javascript
    //if ( ! $("#" + res.task_id).length ) s_num = s_num+1; // Increment s_num for new file
    if (!serial_num[res.task_id]) 
    {
        s_num = s_num+1;
        serial_num[res.task_id] = s_num;
    }
    const taskData = `
      <tr id=${res.task_id}>
        <td>${serial_num[res.task_id]}</td>
        <td>${res.file_id}</td>
        <td>${res.prog}</td>
        <td>${res.tot_spc}</td>
        <td>${res.per_fem}</td>
      </tr>`
//    var elem = document.getElementById(${res.task_id})
    if ( $("#" + res.task_id).length )
    {
        $("#" + res.task_id).replaceWith(taskData);
    } else {
        $("#tasks").before(taskData);
    }

//    $('#tasks').prepend(html);
    const taskStatus = res.task_status;
    if (taskStatus === 'finished' || taskStatus === 'failed') return false;
    setTimeout(function() {
      getStatus(res.task_id);
    }, 1000);
  })
  .fail((err) => {
    console.log(err)
  });
}

// Add the following code if you want the name of the file appear on select
$(".custom-file-input").on("change", function() {
  var fileName = $(this).val().split("\\").pop();
  $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});

// Show submit button only after file is selected
$("#inputfile").change(function(e){
    if (this.files.length > 0){
        $("#submit").show();
    } else {
        $("#submit").hide();
    }
});


$(".collapseExample").collapse({
    'toggle': false

});



// Function to execute after submit is clicked
// AJAX for file upload progress bar
// After upload getStatus is called (recursive)
$(document).ready(function() {
    $('#submit').on('click', function(event) {
        event.preventDefault();
        var formData = new FormData($('form')[0]);
//        $('#ProgressText').remove();
        $('#submit').hide();
        $('#progressBar').show();
        $.ajax({
            xhr: function(){
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable){
                        var percent = Math.round((e.loaded / e.total) * 100);
                        $('#InitProgress').attr('aria-valuenow', percent).css('width', percent + '%').text(percent + '%');
                    }
                });
                return xhr;
            },
            url: $SCRIPT_ROOT + "/_run_task",
            data: formData,
            method: "POST",
            processData: false,
            contentType: false
//            success: function() {
                //alert("File uploaded");
//                }
        })
		.done((res) => {
            $('#progressBar').hide();
            $(".custom-file-input").siblings(".custom-file-label").addClass("selected").html('');
//            document.getElementById("taskTable").rows[1].setAttribute("id", res.task_id);
/*            if (!$('#taskTable').length){
                //$('#FullBody').after(taskTable)
                $('#infographic').after(taskTable)
            } */
			getStatus(res.task_id)
		});    
    });
});
