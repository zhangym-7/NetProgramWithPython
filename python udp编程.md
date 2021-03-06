# python UDP编程
IP协议只保证将数据包（packet）传输至正确的机器。应用程序维护一个会话的话，还需要额外的特性：
 - 多路复用：应用程序需要给数据包打上标签，以便于区分不同的数据包；
 - 可靠传输：数据包在两台主机间进行传输的过程中，发生的任何错误，都需要进行修复； 
 
上述两个特性中，UDP协议只实现了多路复用的特性。UDP通过不同的端口号，对目标为同一主机上的不同服务的数据包进行适当的分解。
虽然支持多路复用，但是使用UDP协议时，仍然需要自行处理丢包、重包及包乱序问题。  
TCP协议实现了上述两个特性，与UDP一样，TCP也是使用端口号进行多路复用及分解。并且还保证了数据流的顺序及可靠性。  

## 端口号
通过IP地址和端口号，网络上的机器之间可以有效的标识源机器及目标机器，即：
```
Source (IP: port number) --> Destination (IP: port number)
```
对于端口号的选择，通常有如下常规方法：
 - 惯例：IANA（互联网号码分配机构，Internet Assigned Number Authority）为许多专用服务分配了官方的知名端口，如SSH
 的22端口，HTTP的80端口；
 - 自动配置：通常而言，计算机在首次连接网络的时候，会使用DHCP这样的协议获取一些重要服务的IP地址，如DNS。应用程序通
 过将这些IP地址与知名端口结合，即可访问响应的基础服务；
 - 手动配置：管理员或用户还可以手动配置IP地址和服务域名；
 
在Linux系统上，可以通过查看`/etc/services`文件获取知名端口（0~1023）的相关信息。
 
## 套接字（socket）
在操作系统底层，网络操作的背后的系统调用都是围绕着socket的概念进行的。socket是一个通信断点，操作系统使用整数标识socket，
在python中使用`socket.socket`对象来表示。
```python
import argparse, socket
from datetime import datetime

MAX_BYTES = 65535


def server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('127.0.0.1', port))
    print "Listening at {}".format(sock.getsockname())
    while True:
        data, address = sock.recvfrom(MAX_BYTES)
        text = data.decode('ascii')
        print "The client at {} says {!r}".format(address, text)
        text = "Your data was {} bytes long.".format(len(data))
        data = text.decode('ascii')
        sock.sendto(data, address)


def client(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    text = "The time is {}".format(datetime.now())
    data = text.encode('ascii')
    sock.sendto(data, ('127.0.0.1', port))
    print "The OS assigned me the address {}".format(sock.getsockname())
    data, address = sock.recvfrom(MAX_BYTES)
    text = data.decode('ascii')
    print "The server {} replied {!r}".format(address, text)

if __name__ == "__main__":
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description="Send and receive UDP locally.")
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('-p', metavar='PORT', type=int, default=1080, help='UDP port(default 1080)')
    args = parser.parse_args()
    function = choices[args.role]
    function(args.p)
```
服务端代码中：
 1. 调用了一次`socket.socket()`，接下来的调用都是围绕着返回的套接字对象进行的，
 在初始化套接字的时候，还标记了特定的协议族：`AF_INET(ipv4)`和数据包类型：`SOCK_DGRAM(UDP协议)`；
 2. 接着使用`bind()`函数绑定一个UDP的网络地址，该地址包含两部分：IP地址（或主机名）及端口号。如果绑定的端口号被占用，
 则会抛出一个异常信息；
 3. 套接字绑定成功后，服务端就进入到准备接收阶段，通过`recvfrom()`函数，不断接收客户端的请求数据，没有请求的时候，
 `recvfrom()`就处于等待状态，`recvfrom()`接收数据报后，会返回两个值：一个是发送该数据报客户端地址，一个是数据报中
 的内容。
 
 在客户端代码中：
 1. 调用`sendto()`函数，传入发送的目标地址和需要发送的数据信息，客户端的端口号由操作系统进行随机分配；

## 混杂客户端和垃圾回复
上述代码中，客户端程序虽然通过`recvfrom()`函数接收了返回的数据，但是，代码中没有检查数据报的来源地址，这样就没有验证该数据是否来源于目标主机。  
上述的这种 **不考虑地址是否正确，接收并处理所有收到的网络数据包的客户端叫做混杂客户端。** 混杂客户端并不是没有适用场景，当我们需要监控到达某一端口的所有数据包，就可以使用混杂客户端。但是，一般而言，混杂存在严重安全问题。  
为了确保客户端能够和正确的服务端通信，可以通过编写良好的加密算法实现。当然还可以通过以下的方式进行：
 - 设计或使用在请求中包含唯一标识符或请求ID的协议，在响应中重复特定请求的唯一标识符或请求ID；
 - 通过检查响应数据包的地址与请求数据包的地址是否相同；

## 不可靠性、退避、阻塞和超时
在真实的网络环境中，数据包随时存在丢失的可能。在UDP协议中，不可靠性意味着客户端需要在一个循环内发送请求。对于客户端而言，有两种处理请求的方式：
 - 客户端一直等待某个请求的响应；
 - 客户端在等到足够长的时间后，重新发送一个新的请求。  

对于客户端而言，服务端的响应存在多种可能，但是客户端并不能有效的区分每种可能的情况，因此，合理的设置客户端超时时间是很有必要的。
在设置了超时时间后，我们仍然需要在响应超时后，进行后续的操作。比如，重新发送请求消息，这时候，如果选用固定的时间点进行消息重发，极有可能造成网络拥塞（网络拥塞也是数据包丢失的主要原因）。此时可以采用一种称为 **指数退避** 的方式进行消息重发，即重发消息的频率以指数级降低，直到网络状态恢复。
在上述操作中，客户端的请求在等待着网络操作的完成，这个过程我们称为请求调用阻塞`(block)`了客户端。
