from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import os
import sys
from pathlib import Path

def primary(conn: socket)->None:
    #Asks for file name as input, loops until user inputs "quit"
    fileNames = input("Please input the name of the files (separated by spaces) you would like to request (or \"quit\" to exit): ")

    while fileNames.lower() != "quit":
        for fileName in fileNames.split():
            #Checks if the file already exists, skips to next iteration if so
            if Path(os.path.join(sys.path[0], fileName)).is_file():
                print(f"{fileName} already exists")
                #fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")
                continue
            
            #Creates request message for server (REQ fileName) and sends it
            message = "REQ " + fileName
            conn.sendall(message.encode('utf-8'))

            print(f"Requested {fileName}")

            #Receives first set of bytes from server
            contents = bytearray(conn.recv(1024))

            #Decodes tail, either NEF (not end file) or EOF (end of file)
            tail = contents[-3:]
            tailStr = tail.decode('utf-8')

            #Checks if the file was found in the server or client 2, advances if not
            if tailStr == "ERR":
                print(f"{fileName} not found")
                #fileName = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")
                continue

            f = open(os.path.join(sys.path[0], fileName), "wb")

            #Removes tail from contents and writes to file
            contents = contents[: len(contents) - 3]
            f.write(contents)

            #Continues to receive file until tail is "EOF", repeats above code
            while tailStr != "EOF":
                contents = bytearray(conn.recv(1024))

                tail = contents[-3:]
                tailStr = tail.decode('utf-8')

                contents = contents[: len(contents) - 3]
                f.write(contents)

            f.close()

            print(f"Received {fileName}")

            #Sends acknowledgement to server (ACK fileName)
            conn.sendall(("ACK " + fileName).encode('utf-8'))

            print(f"Acknowledged {fileName}")

        #Asks for next iteration's input
        fileNames = input("Please input the name of the file you would like to request (or \"quit\" to exit): ")

    #After user inputs "quit", sends message cancelling program to server and closes connection
    message = "END"
    conn.sendall(message.encode('utf-8'))

    conn.close()

def secondary(conn: socket)->None:
    #Receives request from server
    request = conn.recv(2048).decode("utf-8")

    #Makes sure that request actually received something, skips if it didn't
    if sys.getsizeof(request) >= sys.getsizeof("END"):
        #Loops until server indicates the program is terminated, or until request is invalid
        while request.split()[0] != "END" or sys.getsizeof(request) == 0:
            #If server submitted a valid request (REQ fileName), use the file request function
            if(request.split()[0] == "REQ"):
                #print(f"{request.split()[1]} requested")
                fileRequest(request.split()[1], conn)

            request = conn.recv(2048).decode("utf-8")

    #Close connection with server after receiving "END" or an invalid request
    conn.close()

def fileRequest(fileName: str, conn: socket)->None:
    #Make sure the requested file is valid
    reqFile = Path(os.path.join(sys.path[0], fileName))

    if reqFile.is_file():
        file = open(os.path.join(sys.path[0], fileName), "rb")
        fileSize = os.path.getsize(os.path.join(sys.path[0], fileName))
        currPos = 0

        #Reads first 1021 bytes of the file, increments counter
        contents = bytearray(file.read(1021))
        currPos += len(contents)

        #Appends tail onto contents and sends data to server
        #NEF (not end file) or EOF (end of file)
        if currPos < fileSize:
            contents.extend("NEF".encode('utf-8'))
        else:
            contents.extend("EOF".encode('utf-8'))

        conn.sendall(contents)

        #Loops until entire file has been sent, repeats above code
        while currPos < fileSize:
            contents = bytearray(file.read(1021))
            currPos += len(contents)

            if currPos < fileSize:
                contents.extend("NEF".encode('utf-8'))
            else:
                contents.extend("EOF".encode('utf-8'))

            conn.sendall(contents)

        file.close()
    else:
        #Sends an error to the server if file not found
        message = "File not found"
        conn.sendall((message + "ERR").encode('utf-8'))
        return

def main(hostname: str, port1: int, port2: int)->None:
    #Connects to server
    conn1 = socket(AF_INET, SOCK_STREAM)
    conn1.connect((hostname, port1))

    conn2 = socket(AF_INET, SOCK_STREAM)
    conn2.connect((hostname, port2))

    print("Connected to server")

    primaryThread = Thread(target=primary, args=(conn1,))
    secondaryThread = Thread(target=secondary, args=(conn2,))

    primaryThread.start()
    secondaryThread.start()
    
    primaryThread.join()
    secondaryThread.join()

    print("Exiting")

if __name__ == "__main__":
    #Takes port number and IP address of the server as input
    ip = input("Please input the IPv4 address of the server: ")
    port1 = int(input("Please input the primary port to connect: "))
    port2 = int(input("Please input the secondary port to connect: "))

    main(ip, port1, port2)