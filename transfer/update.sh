
source ../.env

# ./pscp -pw "$PASS" ./../sync/wired/uart_send.cpp "$USER@$HOST1:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../sync/wired/uart_send.cpp "$USER@$HOST2:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../sync/wired/uart_send.cpp "$USER@$HOST3:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../sync/wired/uart_listen.cpp "$USER@$HOST1:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../sync/wired/uart_listen.cpp "$USER@$HOST2:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../sync/wired/uart_listen.cpp "$USER@$HOST3:/home/$USER/Downloads/recordingModule/"

# g++ -o send uart_send.cpp -lwiringPi
# g++ -o list uart_listen.cpp -lwiringPi

./pscp -pw "$PASS" ./../record/record.cpp "$USER@$HOST1:/home/$USER/Downloads/recordingModule/"
./pscp -pw "$PASS" ./../record/record.cpp "$USER@$HOST2:/home/$USER/Downloads/recordingModule/"
./pscp -pw "$PASS" ./../record/record.cpp "$USER@$HOST3:/home/$USER/Downloads/recordingModule/"

# g++ record.cpp -o pr -lasound -pthread -lwiringPi

# ./pscp -pw "$PASS" ./../transfer/automatic/client.py "$USER@$HOST1:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../transfer/automatic/client.py "$USER@$HOST2:/home/$USER/Downloads/recordingModule/"
# ./pscp -pw "$PASS" ./../transfer/automatic/client.py "$USER@$HOST3:/home/$USER/Downloads/recordingModule/"
