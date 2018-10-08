import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from qanta.guesser.tfidf import TfidfGuesser

MODEL_SAVE_DIR = 'tfidf_model'
BUZZ_NUM_GUESSES = 10
BUZZ_THRESHOLD = 0.3

def create_handler_class():

    #loading the model
    tfidf_guesser = TfidfGuesser.load(MODEL_SAVE_DIR)

    class QA_Handler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs): 
                   
            self.tfidf_guesser = tfidf_guesser
            BaseHTTPRequestHandler.__init__(self,*args, **kwargs)
            
        def _set_headers(self, status=200):
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

        def do_HEAD(self):
            self._set_headers()
        
        def _guess(self, question_text):
            guesses = self.tfidf_guesser.guess([question_text],BUZZ_NUM_GUESSES)[0]
            scores = [guess[1] for guess in guesses]
            buzz = scores[0]/sum(scores) >= BUZZ_THRESHOLD
            return guesses[0][0], buzz

        def do_POST(self):
            if self.path != '/qa':
                self._set_headers(400)
                self.wfile.write(json.dumps('Invalid path!'))
                return
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            print(data_string)
            input_question = json.loads(data_string)
            guess, buzz = self._guess(input_question['question_text'])
            self._set_headers()                                
            self.wfile.write(json.dumps({'guess': guess, 'buzz': True if buzz else False}).encode('utf-8'))
                    
    return QA_Handler

if __name__ == '__main__':        
    
    server_class = HTTPServer
    handler_class = create_handler_class()
    httpd = server_class(('localhost', 80), handler_class)
    print(time.asctime(), 'Server Starts - %s:%s' % ('localhost', 80))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), 'Server Stops - %s:%s' % ('localhost', 80))
