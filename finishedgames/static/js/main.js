
function sendAction(form, actionsToDisplayDivIds, actionsToHideDivIds = []) {
    const xhr = new XMLHttpRequest();

    xhr.timeout = 10000; // ms
    xhr.ontimeout = errorFeedback;
    xhr.onabort = errorFeedback;
    xhr.onerror = errorFeedback;
    xhr.onload = () => {
        let div;

        if (xhr.status === 200) {
            for (let divId of actionsToDisplayDivIds) {
                div = document.getElementById(divId);
                div.style.display = "block";
            }
            for (let divId of actionsToHideDivIds) {
                div = document.getElementById(divId);
                div.style.display = "none";
            }
            form.style.display = "none";
            successFeedback();
        } else {
            errorFeedback();
        }
    };

    xhr.open("POST", form.action);
    xhr.send(new FormData(form));
}

function successFeedback() {
}

function errorFeedback() {
    console.log("ERROR");
    alert("There was an error trying to save your action, please try again.");
}
