FROM nginx:alpine

# Remove default nginx config and copy ours
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static frontend files
COPY src /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
