from flask import Flask,render_template,request

from transformers import AutoTokenizer, T5ForConditionalGeneration

from language_tool_python import LanguageTool
tool = LanguageTool('en-US')

from flask_socketio import SocketIO, emit

from googletrans import Translator

app= Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
    
@app.route('/')
def home():
    output=""
    return render_template('index.html',**locals())
@app.route('/summary.html')
def render_summary_page():
    return render_template('summary.html')

@app.route('/summ',methods=['POST'])
def summ():
    input=request.form['data']
    
    multi_string=""" """+input
    tokenizer = AutoTokenizer.from_pretrained('t5-small')
    model = T5ForConditionalGeneration.from_pretrained('t5-small')
    encoded_tokens = tokenizer.encode("summarize: " + multi_string, return_tensors='pt', max_length=512, truncation=True)
    summary_ids = model.generate(encoded_tokens, max_length=150, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    
    return render_template('summary.html',original_text=input,output=summary)

@app.route('/grammar.html')
def grammer_page():
    return render_template('grammar.html')


@app.route('/check_grammar',methods=['POST'])
def check_grammar():
    
    text=request.form['incorrect_text']
    incorrect_text=text
    
    matches = tool.check(text)
    for match in reversed(matches):
        start = match.offset
        end = match.offset + match.errorLength
        text = text[:start] + match.replacements[0] + text[end:]
        
    return render_template('grammar.html',original_text=incorrect_text,output=text)
    
@socketio.on('input_text')
def handle_input(input_text):
    # Process the input text to identify and highlight errors
    matches = tool.check(input_text)
    errors = []
    for match in matches:
        errors.append({
            'message': match.message,
            'offset': match.offset,
            'length': match.errorLength,
            'replacements': match.replacements
        })
    
    # Emit the highlighted text with error information back to the front-end client
    emit('output_text', {'input_text': input_text, 'errors': errors})
    
    
    
    
@app.route('/trans.html')
def run_lang():
    return render_template('trans.html')    
    
    
@app.route('/trans',methods=['POST'])
def translate():
    translator = Translator(service_urls=['translate.google.com'])
    english_text=request.form['data']
    selected_lang=request.form['selected_lang']
    if selected_lang=='hindi':
        dest='hi'
    elif selected_lang=='bengali':
        dest='bn'
    elif selected_lang=='french':
        dest='fr'
        
    translated_text=translator.translate(english_text, dest).text
    return render_template('trans.html',original_text=english_text,output=translated_text)

if __name__ == '__main__':
    socketio.run(app)
