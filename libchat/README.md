
# A Universal Chat History Management

## Fields

Table Message:
+ source(enum): can be 0:wechat, ...
+ time(time)
+ sender: id of the sender. id follows the name convention of source
+ chatroom: id of the chatroom (can be a private chat with a sender, or a group chat)
+ text: text content. emojis are encoded according to the source
+ image: binary of the image.
+ sound: binary of an audio
+ extra_data: other possible data specific to the source.

Table Wechat:
+ avatars
+ nicknames
+ emojis
