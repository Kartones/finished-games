
function sendAction(divId, oppositeActiondivId) {
    const form = document.querySelector("#" + divId + " form");
    const xhr = new XMLHttpRequest();

    xhr.timeout = 10000; // ms
    xhr.ontimeout = errorFeedback;
    xhr.onabort = errorFeedback;
    xhr.onerror = errorFeedback;
    xhr.onload = () => {
        if (xhr.status === 200) {
            let oppositeActionDiv = document.getElementById(oppositeActiondivId);
            oppositeActionDiv.style.display = "block";
            document.getElementById(divId).style.display = "none";
        } else {
            errorFeedback();
        }

    };

    xhr.open("POST", form.action);
    xhr.send(new FormData(form));
}

function errorFeedback() {
    console.log("ERROR");
}
