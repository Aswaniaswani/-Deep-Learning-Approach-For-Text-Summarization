from distutils.log import debug
from nltk.corpus import stopwords
import numpy as np
import networkx as nx
import regex
from flask import Flask, request, jsonify, render_template
import nltk
from fpdf import FPDF
from werkzeug.utils import secure_filename
import os
import pytesseract
from PIL import ImageFilter
from PIL import Image
#nltk.download('stopwords')

#from win32com.client import Dispatch
#speak=Dispatch("SAPI.SpVoice").Speak

#import win32api
#win32api.FormatMessage(-2147221008)

def read_article(data):
    
    article = data.split(".")
    sentences = []
    for sentence in article:
        review = regex.sub("[^A-Za-z0-9]"," ", sentence)
        sentences.append(review.replace("[^a-zA-Z]", " ").split(" "))
    sentences.pop()
    return sentences

def sentence_similarity (sent1, sent2, stopwords=None):
    if stopwords is None: 
        stopwords = []

    sent1 = [w.lower() for w in sent1] 
    sent2 = [w.lower() for w in sent2]

    all_words = list(set(sent1 + sent2))

    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)

    #build the vector for the first sentence
    for w in sent1:
        if w in stopwords:
            continue
        vector1[all_words.index(w)] += 1

    # build the vector for the second sentence
    for w in sent2:
        if w in stopwords:
            continue
        vector2[all_words.index(w)] += 1

    return 1 - nltk.cluster.util.cosine_distance(vector1, vector2)

def build_similarity_matrix(sentences, stop_words):
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))

    for idx1 in range(len(sentences)):
        for idx2 in range(len(sentences)):
            if idx1== idx2: #ignore if both are same sentences
                continue
            similarity_matrix[idx1][idx2] = sentence_similarity(sentences[idx1], sentences[idx2], stop_words)

    return similarity_matrix

def generate_summary(file_name, top_n=10):
    stop_words = stopwords.words("english") 
    summarize_text = [] 

    #Step 1 Read text and split it
    sentences = read_article(file_name)

    #Step 2 - Generate Similary Martix across sentences 
    sentence_similarity_martix = build_similarity_matrix(sentences, stop_words) 

    # Step 3 - Rank sentences in similarity martix
    sentence_similarity_graph = nx. from_numpy_array(sentence_similarity_martix)
    scores = nx.pagerank(sentence_similarity_graph)
    
    # Step 4 - Sort the rank and pick top sentences
    ranked_sentence = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True) 
    # print("\n\n---- ----\nIndexes AnIndexes of top ranked sentence order are ", ranked sentence) ranked_sentence)

    for i in range(top_n):
        summarize_text.append(" ".join(ranked_sentence[i][1]))



    a=" . ".join(summarize_text)
    return a 

#-------------------------FLASK------------------------------------#

app= Flask(__name__)

app.config['UPLOAD_FOLDER'] = './media'

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

@app.route('/template', methods =['POST'])
def original_text_form():
    text = request.form['input_text']
    number_of_sent = request.form['num_sentences']
    print("TEXT:\n" ,text)
    summary = generate_summary(text,int(number_of_sent))
    print(summary)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 15)
    pdf.cell(200, 10, txt = summary,ln=1 , align = 'J')
    name=input("enter pdf name: ")
    pdf=pdf.output("name.pdf")
   
    return render_template('summary.html', title="summarizer",original_text = text, output_summary = summary, num_sentences = 5,pdf=pdf)

@app.route('/imagesum', methods =['POST'])
def imagesum():
    texts = request.form['result']
    number_of_sent = request.form['num_sentences']
    print("text:\n" ,texts)
    summary = generate_summary(texts,int(number_of_sent))
    
    return render_template('image.html', title="summarizer",original_text = texts, output_summary = summary, num_sentences = 5)

# @app.route('/txt')
# def txt():
#     # speak(summary)
#     text = request.form['input_text']
#     number_of_sent = request.form['num_sentences']
#     print("TEXT:\n" ,text)
#     summary = generate_summary(text,int(number_of_sent))
#     # save FPDF() class into a
#     # variable pdf
#     print(summary)
#     pdf = FPDF()

#     # Add a page
#     pdf.add_page()

#     # set style and size of font
#     # that you want in the pdf
#     pdf.set_font("Arial", size = 15)
    
#     # create a cell
#     pdf.cell(200, 10, txt = summary,ln=3 , align = 'J')


#     # save the pdf with name .p
#     name=input("enter pdf name: ")

#     pdf.output(name+".pdf")

#     return render_template('pdf.html')
@app.route('/word')
def word():
    title = "Text summarizer"
    return render_template('nwordsummary.html',title = title)

@app.route('/image')
def image():
    title = "Text summarizer"
    return render_template('image.html',title = title)

@app.route('/test')
def test():
    title = "Text summarizer"
    return render_template('summary.html',title = title)

@app.route('/')
def homepage():
    title = "Text summarizer"
    return render_template('index.html',title = title)

@app.route('/submitImage/',methods=['POST',])
def submitImage():
    image = request.files['ocrImage']
    text = ''
    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    text = pytesseract.image_to_string(img)
    f = open(os.path.join(app.config['UPLOAD_FOLDER'], filename)+'.txt','w')
    f.write(text)
    f.close()
    return render_template('textFile.html',text=text,filename=f)


if __name__ == "__main__":
    app.run(debug=True)