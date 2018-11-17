pymqiwm : What You Need From Pymqi
==========================

pymqiwm is focused on making interaction of the user with the IBM MQ 
infrastructure easier.

![image](easy.jpg)

How easy is it your ask? here's an answer:

``` {.sourceCode .python}
>>> with queue:
>>>     for message in queue.browse_messages():
>>>         print(message)
will iterate over all message in the queue and print them one by one
>>>     queue.put("test message")
>>>     queue.get()
b"test message"
>>>     
>>> with qmgr:
>>>     qmgr.create_local_queue(name="LOCAL")
```

Pymqi lets you hide all the complicated interface wit the pymqi package
behind easy to understand and easy to use functions.

Feature Support
---------------

-   Easy to understand interface
-   Making business logic much more clearer
-   Never leaving open handlers (`with` context managers)
-   Enables to put and get messages from queue whenever you want 
(which is not the case with pymqi, gotta handle different `open` options)
Requests officially supports Python 2.7 & 3.4–3.7, and runs great on
PyPy.

How to Contribute
-----------------

1.  Fork [the repository](https://github.com/Hyaxia/pymqiwm) on
    GitHub to start making your changes to the **master** branch (or
    branch off of it).
2.  Send a pull request.

Pymqi
-----

This repository is using the [pymqi](https://github.com/dsuch/pymqi) package, recommend you check it out.


