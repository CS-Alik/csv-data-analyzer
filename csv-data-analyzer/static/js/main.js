document.addEventListener("DOMContentLoaded", function () {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("csv_file_input");
  const uploadForm = document.getElementById("upload-form");
  const fileNameLabel = document.getElementById("chosen-file-name");

  if (!dropzone || !fileInput || !uploadForm) return;

  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    if (files.length) {
      fileInput.files = files;
      handleFileChosen(files[0]);
      uploadForm.submit();
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
      handleFileChosen(fileInput.files[0]);
      uploadForm.submit();
    }
  });

  function handleFileChosen(file) {
    if (fileNameLabel) {
      fileNameLabel.textContent = "Uploading " + file.name + " ...";
    }
    const chooseBtn = dropzone.querySelector(".upload-choose-btn");
    if (chooseBtn) {
      chooseBtn.disabled = true;
      chooseBtn.textContent = "Uploading...";
    }
  }
});