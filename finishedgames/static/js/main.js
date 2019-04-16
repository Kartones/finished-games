let feedbackTimeoutID;

function sendAction(form, actionsToDisplayDivIds, actionsToHideDivIds = []) {
    const xhr = new XMLHttpRequest();

    xhr.timeout = 10000; // ms
    xhr.ontimeout = errorFeedback;
    xhr.onabort = errorFeedback;
    xhr.onerror = errorFeedback;
    xhr.onload = () => {
        let div;

        if (xhr.status === 200 || xhr.status === 204) {
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

function hideFeedback() {
    feedbackDiv = document.getElementById("feedback");
    feedbackDiv.style.display = "none";
    clearInterval(feedbackTimeoutID);
}

function successFeedback() {
}

function errorFeedback() {
    feedbackDiv = document.getElementById("feedback");
    feedbackDiv.style.display = "block";
    feedbackTimeoutID = setInterval(hideFeedback, 8000);
}
