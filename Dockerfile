FROM lambci/lambda:build-python3.6
RUN pip install --upgrade pip
RUN yum -y remove cmake
RUN pip install cmake --upgrade
RUN yum -y install poppler-cpp-devel