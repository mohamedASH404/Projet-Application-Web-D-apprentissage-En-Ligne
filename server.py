from fonctions import *
from flask import Flask, render_template, redirect, url_for, request, session
from flask_socketio import *
from hashlib import sha512
import os


app = Flask(__name__)
app.secret_key = "super secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app)

host = '127.0.0.1'
port = 8888
sequencesCourantes = {} 

############################################### ROUTES ###############################################


@app.route("/")
@app.route("/index")
def index():
    try:
        name=None
        if session['user_type'] == "prof":
            name = session['user']
        elif session['user_type'] == "etudiant":
            jsonEtu = json.loads(session['user'])
            name = jsonEtu['nom'] + " " + jsonEtu['prenom']
        return render_template("index.html", name=name)
    except KeyError:
        return render_template("index.html", name=None)


@app.route("/logout")
def logout():
    session.pop('user', None)
    session.pop('user_type', None)
    return redirect(url_for('index'))


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        data = get_data()
        login = request.form['login']
        password = request.form['password']
        password = password.encode()
        password_sign = sha512(password).hexdigest()
        for users in data:
            if users['user'] == login and users['password'] == password_sign:
                session['user'] = login
                session['user_type'] = "prof"
                return redirect(url_for('questions'))
        return render_template("login.html", error="Login ou mot de passe incorrect")
    else:
        return render_template("login.html")


@app.route("/inscription", methods=['POST', 'GET'])
def inscription():
    if request.method == 'POST':
        data = get_data()
        login = request.form['login']
        password = request.form['password']
        #creation et hashage du mot de passe de reference
        password = password.encode()
        password_sign = sha512(password).hexdigest()
        for users in data:
            if users['user'] == login:
                return render_template("inscription.html", error="Login déjà utilisé")
        data.append({
            "user": login,
            "password": password_sign,
            "questions": []
        })
        write_data(data)
        return redirect(url_for('login'))
    else:
        return render_template("inscription.html")


@app.route("/questions")
def questions():
    try:
        if session['user_type'] == "prof":  
            name = session['user']
            try:
                questions = get_questions(name)
            except:
                session.pop('user', None)
                return redirect(url_for('index'))
            return render_template("questions.html", name=name, questions=questions, length=len(questions), message=request.args.get('message') or "")
        return render_template("index.html", name=None, error="Vous devez être connecté")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route("/del_question/<int:id_question>")
def del_question(id_question):
    try:
        if session['user_type'] == "prof":
            name = session['user']
            data = get_data()
            user_id = get_prof_id(name)
            data[user_id]['questions'].pop(id_question)
            write_data(data)
            return redirect(url_for('questions', message="Question supprimée avec succès"))
        return render_template("index.html", name=None, error="Vous devez être connecté")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route("/traiter_type", methods=['POST', 'GET'])
def traiter_type():
    if request.method == 'POST':
        type = request.form['type']
        etiquettes_existantes = get_etiquettes()
        return render_template("add_question.html", etiquettes_existantes=etiquettes_existantes, type=type)
    else:
        return render_template("choixType.html")


@app.route("/add_question", methods=['POST', 'GET'])
def add_question():
    try:
        if session['user_type'] == "prof":
            if request.method == 'POST':
                data = get_data()
                text = request.form['text']
                titre = request.form['titre']
                type_question = request.form['type']
                question_id = create_unique_id(
                    len(get_questions(session['user'])), session['user'])
                try:
                    etiquettes = json.loads(request.form['etiquettes'])
                except:
                    etiquettes = []
                if type_question == "ChoixMultiple":
                    try:
                        answers = json.loads(request.form['answers_json'])
                    except:
                        answers = []
                elif type_question == "Alphanumerique":
                    try:
                        answers = request.form['rep']
                    except:
                        answers = ""
                elif type_question == "libre" : 
                    answers = ""
                    
                user = session['user']
                question = {
                    "type": type_question,
                    "text": text,
                    "etiquettes": etiquettes,
                    "answers": answers,
                    "titre": titre,
                    "id": question_id
                }
                data[get_prof_id(user)]['questions'].append(question)
                majListeEtiquettes(etiquettes)
                write_data(data)
                return redirect(url_for('questions', message="Question créée avec succès"))
            else:
                etiquettes_existantes = get_etiquettes()
                return render_template("add_question.html", etiquettes_existantes=etiquettes_existantes)
        else:
            return render_template("index.html", name=None, error="Vous devez être connecté")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route("/edit_question/<int:id_question>", methods=['POST', 'GET'])
def edit_question(id_question):
    try:
        if session['user_type'] == "prof":
            if request.method == 'POST':
                data = get_data()

                text = request.form['text']
                titre = request.form['titre']
                try:
                    etiquettes = json.loads(request.form['etiquettes'])
                except:
                    etiquettes = []
                type_question = request.form['type']
                if type_question == "ChoixMultiple":
                    try:
                        answers = json.loads(request.form['answers_json'])
                    except:
                        answers = []
                elif type_question == "Alphanumerique":
                    try:
                        answers = request.form['rep']
                    except:
                        answers = ""
                elif type_question == "libre":
                    answers = ""

                user = session['user']
                user_id = get_prof_id(user)
                id_question = int(request.form['id_question'])
                id_question_unique = request.form['id_question_unique']
                question = {
                    "type": type_question,
                    "text": text,
                    "etiquettes": etiquettes,
                    "answers": answers,
                    "titre": titre,
                    "id": id_question_unique
                }

                data[user_id]['questions'][id_question] = question
                write_data(data)
                majListeEtiquettes(etiquettes)
                return redirect(url_for('questions', message="Question modifiée avec succès"))
            else:
                name = session['user']
                questions = get_questions(name)
                etiquettes_existantes = get_etiquettes()
                return render_template("edit_question.html", name=name, question=questions[id_question], id_question=id_question, etiquettes_existantes=etiquettes_existantes)
        return render_template("index.html", name=None, error="Vous devez être connecté")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route("/visualiser/<int:id_question>")
def visualiser(id_question, question=None):
    try:
        if session['user_type'] == "prof":
            name = session['user']
            if question == None:
                question = get_questions(name)[id_question]
                question = traiter_question(question)
            return render_template("visualiser.html", question=question)
        return render_template("index.html", name=None, error="Vous devez être connecté")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route("/visualiser_temp", methods=['POST'])
def visualiser_temp():
    try:
        if session['user_type'] == "prof" and request.method == 'POST':
            question = json.loads(request.form['question_json'])
            question = traiter_question(question)
            return render_template("visualiser.html", question=question)
        return render_template("index.html", name=None, error="Vous devez être connecté")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route('/generation', methods=['GET', 'POST'])
def generation():
    try:
        if session['user_type'] == "prof":
            name = session['user']
            all_questions = get_questions(name)
            if request.method == 'POST':
                filtres = request.form.getlist('filtres')
                questions = get_questions(name, filtres)
            else:
                filtres = []
                questions = all_questions
            liste_filtre = get_etiquettes(all_questions)
            for filtre_applique in filtres:
                liste_filtre.remove(filtre_applique)
            return render_template('generation.html', name=name, questions=questions, filtres=filtres, liste_filtre=liste_filtre)
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur")

@app.route('/generation_temp')
def generation_temp():
    try:
        if session['user_type'] == "prof":
            return render_template('generation_temp.html')
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur")

@app.route('/controle', methods=['GET', 'POST'])
def controle():
    try:
        if session['user_type'] == "prof":
            if request.method == 'POST':
                # Récupération des données du formulaire
                anonyme = request.form['identification']
                if anonyme == "identifies":
                    anonyme = False
                else:
                    anonyme = True
                ordre = request.form['ordre']
                if ordre == "tri":
                    ordre = "ordre"
                else:
                    ordre = "aleatoire"
                nb_questions = int(request.form['nb_questions'])
                nb_controles = int(request.form['nb_controles'])
                composition = json.loads(request.form['composition'])
                for etiquette, bornes in composition.items():
                    composition[etiquette] = (int(bornes[0]), int(bornes[1]))

                questions = get_questions(session['user'])

            
                # Générer le controle
                try:
                    controles = generer_n_controles(nb_controles, nb_questions, composition, questions, ordre)
                except Exception as exc:
                    # Si problème de génération, retourner à la page de création de contrôle avec détail de l'erreur
                    etiquette_dict = {}
                    for question in questions:
                        for etiquette in question['etiquettes']:
                            if etiquette in etiquette_dict:
                                etiquette_dict[etiquette] += 1
                            else:
                                etiquette_dict[etiquette] = 1
                    etiquettes = []
                    for etiquette, nb in etiquette_dict.items():
                        etiquettes.append({"etiquette": etiquette, "nb": nb})
                    return render_template("controle.html", etiquettes=etiquettes, error=exc)
                # Retourner une page avec le controle
                for controle in controles:
                    for question in controle:
                        question = traiter_question(question)
                return render_template("SHOW_controle.html", controles=controles, anonyme=anonyme)
            else:
                questions = get_questions(session['user'])
                etiquette_dict = {}
                for question in questions:
                    for etiquette in question['etiquettes']:
                        if etiquette in etiquette_dict:
                            etiquette_dict[etiquette] += 1
                        else:
                            etiquette_dict[etiquette] = 1
                etiquettes = []
                for etiquette, nb in etiquette_dict.items():
                    etiquettes.append({"etiquette": etiquette, "nb": nb})
                return render_template("controle.html", etiquettes=etiquettes)
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur1")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur2")

@app.route('/show', methods=['POST'])
def show():
    try:
        if session['user_type'] == "prof":
            name = session['user']
            questions = get_questions(name)
            if request.method == 'POST':
                tabChoix = request.form.getlist('choisi')
                questions_a_generer = []
                for id in tabChoix:
                    new_question = questions[int(id)]
                    new_question = traiter_question(new_question)
                    questions_a_generer.append(new_question)
            return render_template("SHOW.html", name=name, questions=questions_a_generer)
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur")


@app.route('/creation-comptes-etudiants', methods=['GET', 'POST'])
def creation_comptes_etudiants():
    try:
        if session['user_type'] == "prof":
            if request.method == 'POST':
                csv_file = request.files['csv_file']
                if csv_file.filename == '':
                    return redirect(request.url)
                filename = csv_file.filename
                if filename.rsplit('.', 1)[1].lower() != 'csv':
                    return redirect(request.url)
                csv_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                creer_comptes_etudiant(filename)
                return redirect(url_for('index'))
            return render_template('creation_comptes_etudiants.html')
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")


@app.route('/sequence', methods=['GET', 'POST'])
def sequence():
    try:
        if session['user_type'] == "prof":
            prof = session['user']
            questions = get_questions(prof)
            if request.method == 'POST':
                if len(request.form.getlist('filtres')) > 0 :
                    filtres = request.form.getlist('filtres') 
                    questions = get_questions(prof, filtres)
                elif len(request.form.getlist('choisi')) > 0 :
                    tabChoix = request.form.getlist('choisi')
                    questions_sequence = []
                    for id in tabChoix:
                        questions_sequence.append(traiter_question(questions[int(id)]))
                    sequence = SequenceDeQuestions(prof, questions_sequence)
                    sequencesCourantes[sequence.id_unique] = sequence 
                    return redirect(url_for('live', id_sequence=sequence.id_unique))
            else : 
                filtres = []
                questions = questions
            liste_filtre = get_etiquettes(questions)
            for filtre_applique in filtres:
                liste_filtre.remove(filtre_applique)        
            return render_template('diffusion.html', questions=questions, filtres=filtres, liste_filtre=liste_filtre)
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page 1")



################################################ ELEVES ################################################


@app.route("/login-etudiant", methods=['POST', 'GET'])
def login_etudiant():
    if request.method == 'POST':
        data = get_etudiants()
        login = request.form['login']
        password = request.form['password']
        
        for etudiant in data:
            if try_login_etudiant(login, password, etudiant):
                session['user'] = json.dumps(etudiant)
                session['user_type'] = "etudiant"
                return redirect(url_for('wait'))
        return render_template("login_etudiant.html", error="Login ou mot de passe incorrect")
    else:
        return render_template("login_etudiant.html")


@app.route("/logoutEtd")
def logoutEtd():
    session.pop('user_type', None)
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route("/changePass", methods=['POST', 'GET'])
def changePass():
    try:
        if session['user_type'] == "etudiant":
            if request.method == 'POST':
                etudiant = json.loads(session['user'])
                nouveau = request.form['nouveau']
                confirmer = request.form['confirmer']
                if nouveau == confirmer:
                    data = get_etudiants()
                     #creation et hashage du mot de passe de reference
                    password = nouveau.encode()
                    password_sign = sha512(password).hexdigest()
                    for etd in data:
                        if etd['nom'] + "." + etd['prenom'] == etudiant['nom'] + "." + etudiant['prenom']:
                            etd['password'] = password_sign
                            write_data_etudiant(data)
                            return redirect(url_for('wait'))
                else:
                    return render_template("changePass.html", error="Vous avez la mémoire courte dis donc ! Veuillez réessayer.")
            else:
                return render_template("changePass.html")
        else:
            return render_template("index.html", name=None, error="Vous devez être connecté")
    except Exception:
        return render_template("index.html", name=None, error="Vous devez être connecté")


@app.route("/wait")
def wait():
    try:
        if session['user_type'] == "etudiant":
            return render_template("wait.html", etudiant=json.loads(session['user']))
        return render_template("index.html", name=None, error="Vous devez être connecté en tant qu'étudiant pour accéder à cette page")
    except Exception:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant qu'étudiant pour accéder à cette page")

################################################ SOCKET ################################################


@app.route('/live/<string:id_sequence>', methods=['GET'])
def live(id_sequence):
    if id_sequence not in sequencesCourantes:
        return redirect(url_for('index', error="Cette séquence n'existe pas."))
    sequence = sequencesCourantes[id_sequence]
    if session['user_type'] == "etudiant":
        etudiant = json.loads(session['user'])
        return render_template('live_etudiant.html', etudiant=etudiant, sequence=sequence)
    elif session['user_type'] == "prof":
        return render_template('live_prof.html', etudiant=False, sequence=sequence, questions=sequence.getAllQuestions(), length=len(sequence.getAllQuestions()))
    else :
        return render_template("index.html", name=None, error="Vous devez être connecté pour accéder à cette page")


@socketio.on('connect-prof')
def connect_prof(data):
    sid = data["sequence_id"]
    print(f"Prof connecté à la séquence {sid}")
    join_room(sid)
    emit('refresh-connects', {'connects': len(sequencesCourantes[sid].getEtudiants())}, room=sid)
    question = sequencesCourantes[sid].getQuestionCourante().copy()
    emit('display-question', question, room=sid) # Envoie la question courante au prof
    emit('refresh-answers', sequencesCourantes[sid].getNbReponsesCourantes(), room=sid) # Rafraichissement des stats pour le prof

@socketio.on('connect-etu')
def connect_etu(data):
    sid = data["sequence_id"]
    num = data["numero_etudiant"]
    sequencesCourantes[sid].ajouterEtudiant(num)
    print(f"Etudiant {num} connecté à la séquence {sid}")
    question = sequencesCourantes[sid].getQuestionCourante().copy()
    emit('display-question', question) # Envoie la question à l'étudiant
    emit('connect-etu', {'count': len(sequencesCourantes[sid].getEtudiants())}, room=sid) # Rafraichissement du nombre d'étudiants connectés côté prof

@socketio.on('send-answer')
def send_answer(data):
    print(data)
    print("Réponse reçue dans send_answer")
    sid = data["sequence_id"]
    num = data["numero_etudiant"]
    answer = data["answers"]
    #try:
    if sequencesCourantes[sid].getQuestionCourante()["question"]["type"] == "libre":
        confirm = sequencesCourantes[sid].ajouterReponse(num, answer)
        emit('confirm-answer', {'confirm': confirm}) # Message de confirmation pour le client etudiant
        print(" Q Courante : ", sequencesCourantes[sid].getQuestionCourante())
        reponses = sequencesCourantes[sid].extract_counts() 
        emit('show-word-cloud', reponses, broadcast=True) 
        
        nbReponses = sequencesCourantes[sid].getNbReponsesCourantes()
        emit('refresh-answers', nbReponses, room=sid)
        
    else : 
        confirm = sequencesCourantes[sid].ajouterReponse(num, answer)
        emit('confirm-answer', {'confirm': confirm}) # Message de confirmation pour le client etudiant
        reponses = sequencesCourantes[sid].getNbReponsesCourantes()
        emit('refresh-answers', reponses, room=sid) # Rafraichissement des stats pour le prof
    #except Exception as e:
     #   emit('error', {'message': str(e)})

@socketio.on('stop-answers')
def stop_answers(data):
    sid = data["sequence_id"]
    sequencesCourantes[sid].fermerReponses()
    typeQuestion = sequencesCourantes[sid].getQuestionCourante()["question"]["type"]
    emit('stop-answers',typeQuestion, broadcast=True)

@socketio.on('show-correction')
def show_correction(data):
    sid = data["sequence_id"]
    correction = sequencesCourantes[sid].getCorrectionCourante()
    print("Correction envoyée")
    emit('show-correction', correction, broadcast=True)
    
@socketio.on('show-word-cloud')
def show_word_cloud(data):
    sid = data["sequence_id"]
    reponses = sequencesCourantes[sid].extract_counts() 
    emit('show-word-cloud', reponses, broadcast=True)


@socketio.on('next-question')
def next_question(data):
    sid = data["sequence_id"]
    continuer = sequencesCourantes[sid].questionSuivante()
    if continuer:
        question = dict(sequencesCourantes[sid].getQuestionCourante())
        print(question)
        emit('display-question', question, broadcast=True)
    else:
        sequencesCourantes.pop(sid)
        leave_room(sid)
        emit('end-sequence-prof', '/sequence', broadcast=True)
        emit('end-sequence-etudiant', '/wait', broadcast=True)

@socketio.on('fermer-sequence')
def fermer_sequence(data):
    sid = data["sequence_id"]
    sequencesCourantes[sid].fermerSequence() 
    sequencesCourantes.pop(sid)   
    emit('fermer-sequence-prof', '/sequence', broadcast=True)
    emit('fermer-sequence-etudiant', '/wait', broadcast=True)

@socketio.on('toggleDisplayAnswers')
def toggleDisplayAnswers(data):
    emit('toggleDisplayAnswers', data, broadcast=True)

    
################################################ ARCHIVES ################################################

@app.route('/archives')
def archives():
    try:
        if session['user_type'] == "prof":
            archives = dict_of_dicts_to_list_of_dicts(get_archives(session['user']))
            return render_template('archives.html', sequences=archives)
        else:
            return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")
    except KeyError:
        return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")

@app.route('/archive/<string:id_sequence>')
def archive(id_sequence):
    try:
        if session['user_type'] == "prof":
            sequence = dict(get_archives(session['user'], id_sequence))
            etudiants = []
            for num_etu in sequence['etudiants']:
                etudiant = get_etudiant(num_etu)
                etudiant['reponses'] = []
                # Comparaison des réponses des étudiants avec les bonnes réponses
                for question in sequence['questions']:
                    if question['type'] == "ChoixMultiple":
                        correct = True
                        for answer in question["answers"]:
                            if (answer['isCorrect'] == "true" and  not etudiant["numero_etudiant"] in sequence["reponses"][question["id"]][answer["text"]]) or (not answer['isCorrect'] == "true" and etudiant["numero_etudiant"] in sequence["reponses"][question["id"]][answer["text"]]):
                                etudiant['reponses'].append(False) # Mauvaise réponse (Au moins 1 mauvaise réponse choisie ou 1 bonne réponse non choisie)
                                correct = False
                                break
                        if correct:
                            etudiant['reponses'].append(True) # Bonne réponse (Toutes les bonnes réponses choisies et aucune mauvaise réponse choisie)
                    elif question['type'] == "Alphanumerique":
                        correct = question['answers']
                        if etudiant['numero_etudiant'] in sequence['reponses'][question['id']][correct]:
                            etudiant['reponses'].append(True) # Bonne réponse
                        else:
                            etudiant['reponses'].append(False) # Mauvaise réponse
                    elif question['type'] == "libre":
                        for answer_text, etu_list in sequence['reponses'][question['id']].items():
                            if etudiant['numero_etudiant'] in etu_list:
                                etudiant['reponses'].append(answer_text)
                                break
                        

                etudiants.append(etudiant)
            return render_template('archive.html', sequence=sequence, sequence_id=id_sequence, etudiants=etudiants)
        else:
            return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")
    except KeyError:
       return render_template("index.html", name=None, error="Vous devez être connecté en tant que professeur pour accéder à cette page")
    
if __name__ == '__main__':
    # Lancement du serveur
    socketio.run(app, host=host, port=port, debug=True)