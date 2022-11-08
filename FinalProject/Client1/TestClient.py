from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import sys

def main(hostname: str, portno: int)->None:
    fileNames = ["test2.txt", "test.txt"]
    
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((hostname, portno))

    for file in fileNames:
        message = "REQ " + file
        conn.sendall(message.encode('utf-8'))

        f = open(os.path.join(sys.path[0], file), "wb")

        contents = conn.recv(1024)
        f.write(contents)
        #while contents.decode('utf-8') != "EOF":
        while sys.getsizeof(contents) >= 1024 and contents.decode("utf-8") != "EOF":
            print(contents.decode('utf-8'))
            
            contents = conn.recv(1024)
            f.write(contents)

        f.close()

        print("sending ack")

        conn.sendall(("ACK " + file).encode('utf-8'))

    message = "END"
    conn.sendall(message.encode('utf-8'))

    conn.close()

if __name__ == "__main__":
    main("localhost", 6060)