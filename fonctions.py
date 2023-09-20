import csv
import json
import markdown2
from bs4 import BeautifulSoup
from hashlib import sha256
import re
from datetime import datetime
from hashlib import sha512
from random import randint, shuffle, choice
import copy
import spacy

nlp = spacy.load("fr_core_news_sm")

UPLOAD_FOLDER = './uploads'


def levenshtein_distance(s, t):
    m, n = len(s), len(t)
    d = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j
    for j in range(1, n + 1):
        for i in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                substitution_cost = 0
            else:
                substitution_cost = 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + substitution_cost)
    return d[m][n]


################################## Fonctions ##################################


class SequenceDeQuestions:
    nb_max_alphanumerique = 4

    def __init__(self, prof, questions):
        if type(questions) != list:
            self.questions = [].append(questions) 
        else:
            self.questions = questions # de la forme [{"id": "id_question", "type": "ChoixMultiple", "question": "Question ?", "answers": [{"text": "Réponse 1", "correct": True}, {"text": "Réponse 2", "correct": False}, {"text": "Réponse 3", "correct": False}]}, {"id": "id_question", "type": "Alphanumerique", "question": "Question ?", "answers": [{"text": "Réponse 1", "correct": True}, {"text": "Réponse 2", "correct": False}, {"text": "Réponse 3", "correct": False}]}]
        if len(questions) == 1:
            self.id_unique = questions[0]["id"]
        else:
            id_string = ""
            for question in self.questions:
                id_string += question["id"]
            self.id_unique = create_unique_id(get_prof_id(prof), id_string)
        self.prof = prof
        self.etudiants = []
        self.etudiants_qui_ont_repondu = []
        # -1 : En attente de démarrage, 0 : Question 1, 1 : Question 2, etc.
        self.etat = 0
        self.reponsesOuvertes = True
        # {id_question : {reponse : [num_etu, num_etu, ...]}}
        self.reponses = {}
        for question in questions:
            self.reponses[question["id"]] = {}
            if question["type"] == "ChoixMultiple":
                for reponse in question["answers"]:
                    self.reponses[question["id"]][reponse["text"]] = []

    def fermerSequence(self):
        self.etat = -2
        self.archiverSequence()

    def questionSuivante(self):
        if self.etat == len(self.questions) - 1:
            self.etat = -2
            self.archiverSequence()
            print(f"Sequence {self.id_unique} archivée avec succès")
            return False
        self.etudiants_qui_ont_repondu = []
        self.etat += 1
        self.ouvrirReponses()
        print(f"Passé à la question {self.etat} / {len(self.questions)}")
        return True

    def fermerReponses(self):
        self.reponsesOuvertes = False

    def ouvrirReponses(self):
        self.reponsesOuvertes = True

    def getQuestionCourante(self):
        return {"question": self.questions[self.etat], "position": self.etat + 1, "total": len(self.questions)} 
        # {'question': {'type': 'libre', 'text': 'LeText', 'etiquettes': [], 'answers': '', 'titre': 'liberté', 'id': 'ac300615'}, 'position': 3, 'total': 3}

    def getAllQuestions(self):
        return self.questions

    def ajouterReponse(self, num_etu, reponse):
        if not self.reponsesOuvertes:
            raise Exception("Les réponses sont fermées.")
        if reponse == []:
            raise Exception("Aucune réponse n'a été donnée.")
        if num_etu in self.etudiants_qui_ont_repondu:
            raise Exception("Vous avez déjà répondu.")
        if self.questions[self.etat]["type"] == "ChoixMultiple":
            for i, reponse_possible in enumerate(self.questions[self.etat]["answers"]):
                if str(i) in reponse and num_etu not in self.reponses[self.questions[self.etat]["id"]][reponse_possible["text"]]:
                    self.reponses[self.questions[self.etat]["id"]
                                  ][reponse_possible["text"]].append(num_etu)
            self.etudiants_qui_ont_repondu.append(num_etu)
            return True
        elif self.questions[self.etat]["type"] == "Alphanumerique":
            reponse = reponse[0]
            if "," in reponse:
                reponse = reponse.replace(",", ".")
            if reponse != "" and not re.match("^[0-9]+(\.[0-9]{0,2})?$", reponse):
                raise Exception(
                    "La réponse n'est pas un nombre avec au plus deux chiffres après la virgule.")
            if str(reponse) not in self.reponses[self.questions[self.etat]["id"]].keys():
                self.reponses[self.questions[self.etat]
                              ["id"]][str(reponse)] = []
                self.reponses[self.questions[self.etat]
                              ["id"]][str(reponse)].append(num_etu)
                self.etudiants_qui_ont_repondu.append(num_etu)
                return True
            elif num_etu not in self.reponses[self.questions[self.etat]["id"]][reponse]:
                self.reponses[self.questions[self.etat]
                              ["id"]][str(reponse)].append(num_etu)
                self.etudiants_qui_ont_repondu.append(num_etu) 
                return True
        else :
            reponse = reponse[0] 
            if str(reponse) not in self.reponses[self.questions[self.etat]["id"]].keys(): 
                self.reponses[self.questions[self.etat]["id"]][str(reponse)] = []
                self.reponses[self.questions[self.etat]["id"]][str(reponse)].append(num_etu) 
                self.etudiants_qui_ont_repondu.append(num_etu)
                return True
            elif num_etu not in self.reponses[self.questions[self.etat]["id"]][reponse]:
                self.reponses[self.questions[self.etat]
                              ["id"]][str(reponse)].append(num_etu)
                self.etudiants_qui_ont_repondu.append(num_etu) 
                return True
        return False

    def getReponsesCourantes(self):
        return self.reponses[self.etat] 
    
    def extract_counts(self): 
        
        if len(self.questions) >1:
            idQ = self.questions[self.etat]["id"]
            reps = self.reponses
            resultat = {}
            for key in reps.keys():
                if key == idQ:
                    resultat[key] = reps[key]
                    break        
            data = resultat
        else :
            data = self.reponses # de la forme {id_question : {reponse : [num_etu, num_etu, ...]}}
        
        counts = {}
        for key, values in data.items(): 
            for answer, numEtu in values.items():
                """
                answer_lemmas = []
                doc = nlp(answer.lower())
                for token in doc:
                    answer_lemmas.append(token.lemma_)
                answer = " ".join(answer_lemmas)
                answer = answer.lower()
                """
                # On compare la réponse avec toutes les clés du dictionnaire
                matches = [] # Liste des réponses qui equivalantes
                for match in counts.keys():
                    if levenshtein_distance(answer, match) <= 2:  # On utilise une limite de 2 modifications
                        if len(numEtu)<=counts[match]:
                            matches.append((match, counts[match], 0))
                        else:
                            matches.append((answer, (counts[match]+len(numEtu)), match))  
                if matches:
                    best_match = max(matches, key=lambda x: x[1])[0]
                    if best_match in counts:
                        counts[best_match] += len(numEtu)
                    else:
                        counts[best_match] = counts[matches[0][2]]
                        counts[best_match] = matches[0][1]
                        del counts[matches[0][2]]
                else:
                    counts[answer] = len(numEtu)
        return counts 

    
    
    def getNbReponsesCourantes(self):
        reponses = dict(self.reponses[self.questions[self.etat]["id"]])
        retour = {}
        retour["answers"] = {}
        total = 0
        if self.questions[self.etat]["type"] == "ChoixMultiple":

            for i, reponse in enumerate(reponses):
                retour["answers"][i] = len(reponses[reponse])
                total += len(reponses[reponse])
            retour["type"] = "ChoixMultiple"

        if self.questions[self.etat]["type"] == "Alphanumerique":
            alphanumerique = {}
            nb_rep_diff = len(reponses)
            for reponse in reponses:
                alphanumerique[reponse] = len(reponses[reponse])
                total += len(reponses[reponse])
            if nb_rep_diff > self.nb_max_alphanumerique:
                alphanumerique = dict(sorted(alphanumerique.items(
                ), key=lambda item: item[1], reverse=True)[:self.nb_max_alphanumerique])
                alphanumerique["Autres"] = total - sum(alphanumerique.values())
            retour["type"] = "Alphanumerique"
            retour["answers"] = alphanumerique
        
        if self.questions[self.etat]["type"] == "libre":
            for reponse in reponses:
                total += len(reponses[reponse])
            retour["type"] = "libre"
            retour["answers"] = reponses
            #total = len(reponses)

        retour["total"] = total
        retour["rep_count"] = len(self.etudiants_qui_ont_repondu)
        return retour

    def getCorrectionCourante(self):
        return self.questions[self.etat]["answers"]

    def getAllReponses(self):
        return self.reponses # de la forme {id_question: {reponse: [num_etu]}}

    def setReponseEtudiant(self, etudiant, reponse):
        if re.match("^[a-zA-Z0-9]{8}$", etudiant) and self.reponsesOuvertes:
            self.reponses[self.questions[self.etat]["id"]][etudiant] = reponse

    def ajouterEtudiant(self, etudiant):
        print("Ajout de l'étudiant " + etudiant)
        if etudiant not in self.etudiants:
            self.etudiants.append(etudiant)

    def getEtudiants(self):
        return self.etudiants

    def archiverSequence(self):
        with open("archive.json", "r") as fp:
            data = json.load(fp)
        try:
            archive_prof = data[self.prof]
        except KeyError:
            data[self.prof] = {}
            archive_prof = {}
        archive_prof[self.id_unique] = {"questions": self.questions, "reponses": self.reponses,
                                        "etudiants": self.etudiants, "date": str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))}
        data[self.prof] = archive_prof
        with open("archive.json", "w") as fp:
            json.dump(data, fp, indent=4)

    def __str__(self) -> str:
        return "SequenceDeQuestions de " + self.prof + " avec " + str(len(self.questions)) + " questions"


def create_unique_id(id, string):
    return sha256(str(id).encode() + string.encode()).hexdigest()[:8]


def get_data():
    """
    Retourne le contenu du fichier prof.json
    Out : data (dict)
    """
    with open('prof.json', 'r') as fp:
        data = json.load(fp)
    return data


def get_etudiants():
    """
    Retourne le contenu du fichier etudiants.json
    Out : data (dict)
    """
    with open('etudiants.json', 'r') as fp:
        data = json.load(fp)
    return data


def get_etudiant(num_etu):
    """
    retourne l'étudiant correspondant au numéro d'étudiant
    In : num_etu (str)
    Out : etudiant (dict)
    """
    data = get_etudiants()
    for etudiant in data:
        if etudiant['numero_etudiant'] == num_etu:
            retour = dict(etudiant)
            del retour['password']
            return retour
    return None


def write_data(data):
    """
    Ecrit dans le fichier prof.json
    In : data (dict)
    """
    with open('prof.json', 'w') as fp:
        json.dump(data, fp, indent=4)


def write_data_etudiant(data):
    """
    Ecrit dans le fichier prof.json
    In : data (dict)
    """
    with open('etudiants.json', 'w') as fp:
        json.dump(data, fp, indent=4)


def get_prof_id(prof):
    """
    Retourne l'id de l'utilisateur dans le fichier prof.json
    In : prof (str)
    Out : id (int)
    """
    data = get_data()
    for i in range(len(data)):
        if data[i]['user'] == prof:
            return i
    return None


def get_questions(prof, filtre=None):
    """
    Retourne la liste des questions de l'utilisateur ayant une etiquette filtre
    In : prof (str)
    In : filtre (list (str)), optionnel : None par défaut
    Out : questions (list (dict)))
    """
    data = get_data()
    if filtre != None:
        questions = []
        for question in data[get_prof_id(prof)]['questions']:
            for etiquette in question['etiquettes']:
                if etiquette in filtre:
                    questions.append(question)
                    break
        return questions
    return data[get_prof_id(prof)]['questions']


# Retourne la liste des etiquettes utilisées dans des questions
# In : questions (list (dict)) (optionnel, si non renseigné, on prend toutes les etiquettes utilisées dans toutes les questions)
# Out : etiquettes (list)


def get_etiquettes(questions=None):
    """
    Retourne la liste des etiquettes utilisées dans des questions
    In : questions (list (dict)) (optionnel, si non renseigné, on prend toutes les etiquettes utilisées dans toutes les questions)
    Out : etiquettes (list)
    """
    if questions == None:
        with open('etiquettes.json', 'r') as fp:
            data = json.load(fp)
    else:
        data = []
        for question in questions:
            for etiquette in question['etiquettes']:
                if etiquette not in data:
                    data.append(etiquette)
    return data


def majListeEtiquettes(listeEtiquettes):
    """
    Met à jour la liste des etiquettes utilisées dans etiquettes.json
    """
    data = get_etiquettes()
    for etiquette in listeEtiquettes:
        if etiquette not in data:
            data.append(etiquette)
    with open('etiquettes.json', 'w') as fp:
        json.dump(data, fp, indent=4)


def clear_etiquettes_non_utilisees():
    """
    Supprime les etiquettes non utilisées dans etiquettes.json
    """
    data = get_etiquettes()
    data2 = get_data()

    # Pour chaque etiquette, si on la trouve dans une question, on la garde sinon on la supprime
    for etiquette in data:
        found = False
        for user in data2:
            if found:
                break
            for question in user['questions']:
                if etiquette in question['etiquettes']:
                    found = True
                    break
        if not found:
            data.remove(etiquette)

    with open('etiquettes.json', 'w') as fp:
        json.dump(data, fp, indent=4)


def generer_id_question():
    """
    Genere un ID à toutes les questions de tous les utilisateurs si elles n'en ont pas
    A supprimer quand les ID fonctionneront parfaitement à la création et modification des questions et que toutes les questions auront un ID
    """
    data = get_data()
    for i in range(len(data)):
        for j in range(len(data[i]['questions'])):
            data[i]['questions'][j]['id'] = create_unique_id(
                j, data[i]["user"])
    write_data(data)


def update_type_question():
    # Met à jour le type des questions. Si c'est QCM Rempalcer par ChoixMultiple
    data = get_data()
    for i in range(len(data)):
        for j in range(len(data[i]['questions'])):
            if data[i]['questions'][j]['type'] == "QCM":
                data[i]['questions'][j]['type'] = "ChoixMultiple"
    write_data(data)


def traiter_texte(texte):
    """
    Traite une chaine de caractère pour la visualiser
    In : texte (str)
    Out : html (str)
    """
    # Markdown et code coloré
    html = markdown2.markdown(texte, extras=[
                              "newline", "fenced-code-blocks", "code-friendly", "mermaid"], safe_mode='escape')
    # Mermaid
    soup = BeautifulSoup(html, 'html.parser')
    for code_block in soup.find_all('code'):
        if "class" not in code_block.parent.parent.attrs:
            new_div = soup.new_tag("div")
            new_div['class'] = "mermaid"
            for line in code_block.contents:
                new_div.append(line)
            code_block.replace_with(new_div)
    return soup.prettify()


def traiter_question(question):
    """
    Traite une question pour la visualiser
    In : question (dict)
    Out : question (dict)
    """
    question["text"] = traiter_texte(question["text"])
    if question["type"] == "ChoixMultiple":
        for answer in question["answers"]:
            answer["text"] = traiter_texte(answer["text"])
    return question


def get_all_num_etu(json_data):
    num_etu = []
    for etu in json_data:
        num_etu.append(etu['numero_etudiant'])
    return num_etu


def creer_comptes_etudiant(filename):
    with open((UPLOAD_FOLDER + "/" + filename), 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    try:
        with open('etudiants.json', 'r') as f:
            data = json.load(f)
    except:
        data = []

    num_existants = get_all_num_etu(data)

    for row in rows:
        if row['numero_etudiant'] not in num_existants:
            row["password"] = ""
            row["prenom"] = row["prenom"].replace(
                " ", "_").replace("'", "_").lower()
            row["nom"] = row["nom"].replace(" ", "_").replace("'", "_").lower()
            data.append(row)

    with open('etudiants.json', 'w') as f:
        json.dump(data, f, indent=4)


def try_login_etudiant(login, password, etudiant):
    if etudiant['nom'] + "." + etudiant['prenom'] == login:
        if etudiant['password'] == "":
            if password == etudiant['numero_etudiant']:
                return True
        else:
            password = password.encode()
            password_sign = sha512(password).hexdigest()
            if password_sign == etudiant['password']:
                return True
    return False


def get_archives(prof, id_sequence=None):
    """
    Retourne les séquences archivées d'un prof
    In : prof (str)
    In : id_sequence (str) (optionnel)
    Out : sequences (list (dict))
    """
    with open('archive.json', 'r') as fp:
        data = json.load(fp)
    try:
        if id_sequence == None:
            return data[prof]
        else:
            return data[prof][id_sequence]
    except:
        return []


def dict_of_dicts_to_list_of_dicts(dict_of_dicts):
    """
    Transforme un dictionnaire de dictionnaires en une liste de dictionnaires
    In : dict_of_dicts (dict (dict))
    Out : list_of_dicts (list (dict))
    """
    list_of_dicts = []
    for key in dict_of_dicts:
        dict_of_dicts[key]['id'] = key
        list_of_dicts.append(dict_of_dicts[key])
    return list_of_dicts


############################################### Generation de controles ################################################

def estQuestionDansListeQuestion(question, listeQuestions):
    """
    Vérifie si une question est dans une liste de questions
    In : question (dict)
    In : listeQuestions (list (dict))
    Out : (bool)
    """
    for q in listeQuestions:
        if q["id"] == question["id"]:
            return True
    return False

def generer_controle(settings, questions, nb_questions):
    """
    In : settings (dict (tuple (int, int))) : Les paramètres des étiquettes, de la forme : {etiquette1 : (min1, max1), etiquette2 : (min2, max2), ...}
    In : questions (dict) : Dictionnaire contenant les questions disponibles
    In : nb_questions (int) : Nombre de questions à générer
    Out : controle (list (dict)) : Le controle généré
    Renvoie un controle généré aléatoirement en fonction des paramètres fournis, avec un nombre de questions par étiquette compris entre les bornes (min, max) fournies dans settings et aucun doublon
    """
    controle = []
    
    # Vérifier que les minimum ne sont pas supérieurs au nombre de questions demandées
    somme_min = sum([settings[key][0] for key in settings])
    if somme_min > nb_questions:
        raise ValueError(f"Minimum de questions ({somme_min}) trop élevé pour créer ce controle de {nb_questions} questions")

    # Vérifier que les maximums de questions demandées ne sont pas inférieurs au nombre de questions demandées restantes après assignation des minimums
    somme_max = sum([(settings[key][1] - settings[key][0]) for key in settings])
    if somme_max < nb_questions - somme_min:
        raise ValueError(f"Le nombre de questions au dessus du minimum ({somme_max}) est trop faible pour créer ce controle de {nb_questions} questions : {nb_questions - somme_min} questions restantes à assigner")

    # Assigner les minimums de questions
    for etiquette, nb in settings.items():
        while nb[0] > 0:
            # Choisit une question au hasard parmi les questions disponibles
            index = randint(0, len(questions[etiquette])-1)
            q = questions[etiquette][index]
            # Vérifie que la question n'est pas déjà dans le controle
            if not estQuestionDansListeQuestion(q, controle):
                # Ajoute la question au controle
                controle.append(q)
                # Supprime la question des questions disponibles
                del questions[etiquette][index]
                nb = (nb[0] - 1, nb[1] - 1)
                nb_questions -= 1
    
    # Assigner les maximums de questions
    while nb_questions > 0:
        # Si il n'y a aucune question disponible pour chaque etiquette demandée, on arrête la boucle et on envoie une erreur
        if not any([len(questions[etiquette]) > 0 for etiquette in settings]):
            raise ValueError(f"Problème d'intersection avec des questions à plusieurs étiquettes sélectionnées : {nb_questions} questions restantes à assigner")
        # Choisit une etiquette au hasard parmi les etiquettes disponibles telle que le max est supérieur à 0
        etiquettes_dispo = [etiquette for etiquette in settings if settings[etiquette][1] > 0]
        etiquette = etiquettes_dispo[randint(0, len(etiquettes_dispo)-1)]
        # Choisit une question au hasard parmi les questions disponibles pour cette etiquette
        index = randint(0, len(questions[etiquette])-1)
        q = questions[etiquette][index]
        # Vérifie que la question n'est pas déjà dans le controle
        if not estQuestionDansListeQuestion(q, controle):
            # Ajoute la question au controle
            controle.append(q)
            # Supprime la question des questions disponibles
            del questions[etiquette][index]
            settings[etiquette] = (settings[etiquette][0], settings[etiquette][1] - 1)
            nb_questions -= 1

    return controle

    
def generer_n_controles(nb_controles, nb_questions, settings, data, mode="aleatoire"):
    """
    Génère un certain nombre de controles
    In : nb_controles (int) Le nombre de controles à générer
    In : nb_questions (int) Le nombre de questions par controle
    In : settings (dict (tuple (int, int))) : Les paramètres des étiquettes, de la forme : {etiquette1 : (min1, max1), etiquette2 : (min2, max2), ...}
    In : data (list (dict)) Les questions
    In : mode (str) Le mode de tri des contrôles. "aleatoire" pour générer des controles avec ordre 100% aléatoire, "ordre" pour garder les quiestions groupées par thème
    Out : tous_controles (list (list (dict))) : La liste des controles générés
    """
    print(f"Creation de controles avec {nb_controles} controles de {nb_questions} questions")
    print(f"Paramètres des étiquettes : {settings}")
    # Création d'un dictionnaire contenant les questions disponibles pour chaque étiquette demandée
    questions_dispo = {}
    for etiquette in settings:
        questions_dispo[etiquette] = []
    
    # Tri des questions par etiquette dans le dictionnaire questions_dispo
    for etiquette in settings:
        for question in data:
            if etiquette in question['etiquettes']:
                questions_dispo[etiquette].append(question)

    # Génération des controles. Générer des controles aléatoirement jusqu'à ce qu'ils soient tous différents
    tous_controles = []
    for i in range(0, nb_controles):
        controle = generer_controle(copy.deepcopy(settings), copy.deepcopy(questions_dispo), nb_questions)
        #Vérification que le nouveau controle ne contient pas les mêmes questions que les autres
        for controle_exist in tous_controles:
            if controle_exist == controle:
                controle = generer_controle(copy.deepcopy(settings), copy.deepcopy(questions_dispo), nb_questions)
        tous_controles.append(controle)
    
    # Spécification sur l'ordre des questions
    if mode == "aleatoire":
        for controle in tous_controles:
            shuffle(controle)
    elif mode == "ordre":
        for controle in tous_controles:
            controle.sort(key=lambda x: x['etiquettes'][0])

    return tous_controles