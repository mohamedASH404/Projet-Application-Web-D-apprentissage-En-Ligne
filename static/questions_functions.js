function addAnswer(text = "", isCorrect = false) {
    // Nouvelle réponse
    let new_answer = document.createElement("div");
    new_answer.style="display:flex; flex-direction: row;justify-content: center;align-items: center; padding: 10px;"
    new_answer.className = "answer form-check form-switch ";
    // Checkbox
    let answerCheckbox = document.createElement("input");
    answerCheckbox.type = "checkbox";
    answerCheckbox.name = "correct";
    answerCheckbox.setAttribute("id", "flexSwitchCheckDefault")
    answerCheckbox.className = "isCorrect form-check-input";
    answerCheckbox.value = isCorrect.toString();
    if (isCorrect.toString() == 'true') {
        answerCheckbox.checked = true;
    }
    answerCheckbox.onclick = function() {
        if (answerCheckbox.checked) {
            answerCheckbox.value = "true";
        } else {
            answerCheckbox.value = "false";
        }
    };
    // Champ de texte
    //<textarea class="form-control form" id="qst" name="text" style="background-color: #EBFCCB;" rows="3" cols="26" placeholder="Ex : Qui est Jonathan ?" required></textarea>
    let answerText = document.createElement("textarea");
    answerText.type = "text";
    answerText.name = "answer_text";
    answerText.placeholder = "Réponse";
    answerText.value = text;
    answerText.className="form-control form";
    answerText.rows = "1";
    answerText.cols = "23";
    answerText.style="background-color: #CBFCF0	; margin-left: 5px";
    answerText.addEventListener("input", function (e) {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";
      });

    // Bouton supprimer
    let answerDelete = document.createElement("button");
    answerDelete.type = "button";
    answerDelete.className = "btn btn-labeled btn-danger";
    answerDelete.onclick = function() {
        new_answer.remove();
    };
    answerDeleteSpan = document.createElement("span");
    answerDeleteSpan.className = "btn-label";
    answerDeleteSpan_i = document.createElement("i");
    answerDeleteSpan_i.className = "fa fa-trash fa-lg";
    answerDelete.style = "margin : 7px;";

    answerDeleteSpan.appendChild(answerDeleteSpan_i)
    answerDelete.appendChild(answerDeleteSpan);
    // Ajout à la réponse des champs
    new_answer.appendChild(answerCheckbox);
    new_answer.appendChild(answerText);
    new_answer.appendChild(answerDelete);
    
    let answers = document.getElementById("answers");
    answers.appendChild(new_answer);
}
function majAnswers() {
    let answers = [];
    let answers_list = document.getElementsByClassName("answer");
    for (let answer of answers_list) {
        let answer_text = answer.children[1].value;
        let answer_correct = answer.children[0].value;
        answers.push({
            "text": answer_text,
            "isCorrect": answer_correct
        });
    }
    let answers_json = document.getElementById("answers_json");
    answers_json.value = JSON.stringify(answers);
}

function addEtiquette() {
    let texte = document.getElementById("input_etiquette").value;
    // Si etiquette vide, ne pas ajouter
    if (texte == "") { 
        return;
    }
    // Si etiquette déjà utilisée, ne pas ajouter
    document.getElementById("input_etiquette").value = "";
    let etiquettes_list = document.getElementsByClassName("etiquette");
    for (let etiquette of etiquettes_list) {
        if (etiquette.id == texte) {
            return; 
        }
    }
    // Ajouter etiquette
    let etiquettes = document.getElementById("etiquettes-list");
    let etiquette = document.createElement("div");
    etiquette.id = texte;
    etiquette.className = "etiquette";
    let etiquetteText = document.createElement("p");
    let etiquetteButton = document.createElement("button");
    etiquetteButton.type = "button";
    etiquetteButton.className = "btn btn-primary btn-sm";
    etiquetteButton.data_bs_toggle = "tooltip";
    etiquetteButton.data_bs_placement = "top";
    etiquetteButton.title = "appuyez pour supprimer";
    etiquetteButton.style="margin: 7px;"
    etiquetteButton.onclick = function() { delEtiquette(texte); };
    etiquetteButton.innerHTML = texte;
    etiquette.appendChild(etiquetteButton);
    etiquettes.appendChild(etiquette);
    majInputEtiquettes()
}
function delEtiquette(id) {
    let etiquettes = document.getElementById("etiquettes-list");
    let etiquette = document.getElementById(id);
    etiquettes.removeChild(etiquette);
    majInputEtiquettes();
};

function majInputEtiquettes() {
    let etiquettes = document.getElementsByClassName("etiquette");
    let inputEtiquettes = document.getElementById("etiquettes");
    let liste = [];
    for (let etiquette of etiquettes) {
        liste.push(etiquette.id);
    }
    inputEtiquettes.value = JSON.stringify(liste);
}

function delFiltre(id) {
    let filtres = document.getElementById("liste-filtre");
    let filtre = document.getElementById(id);
    filtres.removeChild(filtre);
};

function imprimer_page(){
    window.print();
}

function toGreen(checkbox, x) {
    let box = document.getElementById('check'+x);
    if (checkbox.checked) {
      box.style = "margin: 30px; box-shadow: 5px 5px 7px green ; padding: 5px; display:flex ; flex-direction: row; justify-content: center;";
    } else {
      box.style= "margin: 30px; box-shadow: 5px 5px 7px red ; padding: 5px; display:flex ; flex-direction: row; justify-content: center;";
    }
  }

function visualiser() {
    var type_question = document.getElementById("type_question").value;
    if (type_question == "ChoixMultiple") {
        majAnswers();
        var answers = JSON.parse(document.getElementById("answers_json").value);
    } else if (type_question == "Alphanumerique") {
        var answers = document.getElementById("rep").value
    }
    else {var answers = ""}

    var question = {
        "titre": document.getElementById("titre").value,
        "text": document.getElementById("qst").value,
        "type": type_question,
        "answers": answers,
        "etiquettes": document.getElementById("etiquettes").value.split(",")
    }
    var question_json = JSON.stringify(question);
    console.log(question_json);
    document.getElementById("question_json").value = question_json;
}