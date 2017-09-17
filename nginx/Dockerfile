FROM nginx:1.13.5

# Remove the default Nginx configuration file
RUN rm -v /etc/nginx/nginx.conf
RUN rm -v /etc/nginx/conf.d/default.conf

# Copy a configuration file from the current directory
ADD nginx.conf /etc/nginx/

RUN /etc/init.d/nginx restart
