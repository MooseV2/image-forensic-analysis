const submitForm = (e) => {
    e.preventDefault();
    let formData = new FormData(contentForm); // Insert email address
    formData.append("filedata", filePicker.files[0]);
    console.log("Uploading....");

    if (formData.get("filedata") == "undefined" || !validEmail(formData.get("email"))) {
        setState(contentForm, "error");
        return;
    }

    // Do file upload
    const url = '/upload';
    fetch(url, {
        method: 'POST',
        body: formData
    })
        .then((result) => {
            if (result.status == 200) {
                result.text()
                    .then( (text) => {
                        if (text == 'SUCCESS') {
                            console.log(`Upload succeeded: ${text}`);
                            setState(contentForm, "success");
                        } else {
                            console.log(`Upload failed: ${text}`);
                            setState(contentForm, "error");
                        }
                    })
                    .catch((e) => console.log(`Text error ${e}`));
            } else {
                console.log(`Upload failed: ${result.status}`);
                setState(contentForm, "error");
            }

        })
        .catch((e) => {
            console.log(`Upload failed: ${e}`);
            setState(contentForm, "error");
        });
}

const setState = (element, state) => {
    element.classList.remove("error");
    element.classList.remove("warning");
    element.classList.remove("success");
    element.classList.add(state);
}

const validEmail = (email) => {
    // Regular expression to validate email
    return /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email);
}

const fileDragHandler = (e) => {
    // Prevent the browser from attempting to display the file
    e.stopPropagation();
    e.preventDefault();

    // Set file dragover styling
    if (e.type == "dragover") {
        filedrag.classList.add("tertiary");
    } else {
        filedrag.classList.remove("tertiary");
    }
}

const fileSelectHandler = (e) => {
    fileDragHandler(e);
    let files = e.target.files || e.dataTransfer.files;
    filePicker.files = files;

    if (files.length > 0) {
        const fileText = document.getElementById("filetext");
        fileText.innerText = `${files[0].name} - ${files[0].size} bytes`
        const fileIcon = document.getElementById("fileicon");
        fileIcon.classList.add("blue")

    }
}

const filedrag = document.getElementById("filedrag");
const contentForm = document.getElementById("content-form");
const filePicker = document.getElementById("fileselect");

filedrag.addEventListener("dragover", fileDragHandler, false);
filedrag.addEventListener("dragleave", fileDragHandler, false);
filedrag.addEventListener("drop", fileSelectHandler, false);
filePicker.addEventListener("change", fileSelectHandler, false);
contentForm.addEventListener("submit", submitForm, false);

