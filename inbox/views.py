from django.forms import model_to_dict
from django.shortcuts import render
import requests
from accounts.views import decode_cookie
from connections.caches import AuthorCache, Nodes, PostCache
from pages.seralizers import AuthorUserSerializerDB, CommentSerializer, FollowRequestsSerializer, LikeSerializer
from util import AuthorDetail
from posts.models import Comments, Likes, Posts
from posts.serializers import PostsSerializer
from posts.views import format_local_post, format_local_post_from_db, get_object_type
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes, renderer_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from accounts.models import AuthorUser, FollowRequests, ForeignAuthor
from static.vars import ENDPOINT, HOSTS
from .models import Inbox
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from util import get_id_from_url, get_part_from_url, strip_slash
from requests.auth import HTTPBasicAuth
from django.http import HttpResponse, JsonResponse
from django.http import Http404

# VIEW LOGIC FUNCTIONS
# ============================================================================================================================================================

def follow_request_handler(request):
    author_cache = AuthorCache()
    nodes = Nodes()

    requester_id = request.POST.get("requester_id")
    recipient_id = request.POST.get("recipient_id")

    requester_data = author_cache.get(requester_id)
    recipient_data = author_cache.get(recipient_id)

    payload = {
        "type": "Follow",
        "actor": requester_data,
        "object": recipient_data,
        "summary": f"{requester_data['displayName']} wants to follow you."
    }

    inbox_url = f'{recipient_data["url"]}/inbox/'
    safe_host = strip_slash(recipient_data["host"])
    auth = nodes.get_auth_for_host(safe_host)

    try:
        response = requests.post(inbox_url, json=payload, auth=HTTPBasicAuth(auth[0], auth[1]))
        if response.ok:
            return JsonResponse({"status": "success"})
    except Exception as e: 
        print(e)
        return JsonResponse({"status": "error"}, status=400)
    return JsonResponse({"status": "bad response"})

def inbox_post(request, author_id, inbox_index):
    # will be used to display post related to inbox item
    try: 
        author = AuthorUser.objects.get(uuid=author_id)
    except: 
        print("Author not found")
        raise Http404
    
    try: 
        inbox = Inbox.objects.get(author=author)
    except: 
        print("Inbox not found")
        raise Http404
    
    
    if inbox_index not in range(len(inbox.items)):
        print("Inbox index out of range")
        raise Http404

    inbox_item = inbox.items[inbox_index]

    item_type = inbox_item["type"]
    if item_type == "post":
        post_id = inbox_item["id"]

    elif item_type == "comment":
        try: 
            comment = Comments.objects.get(uuid=inbox_item["id"])
        except: 
            print("Comment not found")
            raise Http404

        post_id = comment.post_id

    elif item_type == "like":
        try: 
            like = Likes.objects.get(id=inbox_item["id"])
        except: 
            print("Like not found")
            raise Http404

        post_id = get_part_from_url(like.liked_object, "posts")

    try: 
        post = Posts.objects.get(uuid=post_id)
        author_id = post.author_uuid
        author_cache = AuthorCache()
        author_data = author_cache.get(author_id)
    except: 
        print("Post not found")
        raise Http404

    return render(request, 'posts/dashboard.html', {'all_posts': [format_local_post_from_db(post, author_data)], 'base_url': ENDPOINT})

    
def inbox_view(request):
    # inbox
    author_cache = AuthorCache()
    emptyInbox = False

    try: author = AuthorUser.objects.get(uuid=request.user.uuid)
    except: return render(request, 'errorPage.html', {'errorCode': "404 Author not found"})
    
    try: inbox = Inbox.objects.get(author=author)
    except: emptyInbox = True

    posts = []
    likes = []
    comments = []
    requests = []

    index = 0

    if not emptyInbox:
        for item in inbox.items:
            print(item)
            
            data = None
            if item.get("sender"):
                data = author_cache.get(item["sender"]["uuid"])

            if not data:
                data = {"displayName": "An Unknown Remote Author", 
                        "profileImage": "https://t3.ftcdn.net/jpg/05/71/08/24/360_F_571082432_Qq45LQGlZsuby0ZGbrd79aUTSQikgcgc.jpg"}
                
            if item["type"] == "post":
                try: post = Posts.objects.get(uuid=item["id"])
                except: continue

                author_data = author_cache.get(post.author_uuid)
                post_data = format_local_post_from_db(post)
                post_data["index"] = index
                post_data["author"] = author_data
                posts.append(post_data)

            elif item["type"] == "like":
                try: like = Likes.objects.get(id=item["id"])
                except: continue

                like_data = model_to_dict(like)
                like_data["index"] = index
                like_data["author"] = data
                likes.append(like_data)

            elif item["type"] == "comment":
                try: comment = Comments.objects.get(uuid=item["id"])
                except: continue

                comment_data = model_to_dict(comment)
                comment_data["index"] = index
                comment_data["author"] = data
                comments.append(comment_data)

            elif item["type"] == "follow":
                try: fq = FollowRequests.objects.get(id=item["id"])
                except: continue

                requester = model_to_dict(fq)
                requester["author"] = data
                requests.append(requester)
            
            index += 1
    
    return render(request, 'inbox.html', {'requests_list': requests, 'posts': posts, 'likes': likes, 'comments': comments})


# API
# ============================================================================================================================================================

class InboxItem():
    def __init__(self, itemType, itemID, sender):
        self.itemType = itemType
        self.itemID = itemID
        self.sender = sender
    def formMapping(self):
        return {
            "type": self.itemType,
            "id": self.itemID,
            "sender": self.sender
        }
    def checkSame(self, saved):
        if self.itemType == saved.get("type") and self.itemID == saved.get("id"):
            return True
        return False

# Create your views here.
@swagger_auto_schema(
    methods=['GET'], 
    tags=['inbox'], 
    )
@swagger_auto_schema(
    methods=['POST'], 
    tags=['inbox', 'remote'],
    operation_description="Refer to the following: <a href='https://chimp-chat-1e0cca1cc8ce.herokuapp.com/extra/docs#Inbox'>Section</a>",
    responses={
        200: openapi.Response("Returns the newly created object from the request body."),
        400: openapi.Response("Poorly formatted request body."),
        404: openapi.Response("Author not found."),
    }
)
@swagger_auto_schema(
    methods=['DELETE'], 
    tags=['inbox'], 
    )
@api_view(['GET', 'POST', 'DELETE'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def api_inbox(request, uuid):
    author_cache = AuthorCache()
    try:
        sender_cookie = request.COOKIES.get('ChimpChatToken')
        sender_data = decode_cookie(sender_cookie)
        ad = AuthorDetail(sender_data.get("user_id"), sender_data.get("url"), sender_data.get("host"))
        sender = ad.formMapping()
    except:
        sender = None

    author = get_object_or_404(AuthorUser, uuid=uuid)

    try:
        inbox = Inbox.objects.get(author=author.uuid)
    except Inbox.DoesNotExist:
        inbox = Inbox.objects.create(author=author, items=[])

    if request.method == 'GET':
        if request.user.id != author.id:
            return Response(status=404)
        
        # get a list of posts sent to author_id (paginated)
        posts = []

        for item in inbox.items:
            if item["type"] == "post":
                posts.append(item)

        # check query params for pagination
        page = request.GET.get("page")
        size = request.GET.get("size")
    
        # # if pagination specified, return only the requested range
        if page is not None and size is not None:
            start = (int(page) - 1) * int(size)
            end = start + int(size)
            posts = posts[start:end]

        output = []
        for post_ref in posts:
            try: 
                post = Posts.objects.get(uuid=post_ref["id"])
                post_data = format_local_post(post)
                serializer = PostsSerializer(data=post_data, partial=True)
                # we don't actually need to serialize but it's a good way to ensure we're not returning
                # malformed responses
                if not serializer.is_valid():
                    print(serializer.errors)
                    continue

                output.append(serializer.validated_data)

            except Posts.DoesNotExist: 
                continue
        
        final_data = {"type": "inbox", "author": f"{ENDPOINT}authors/{uuid}", "items": output}
        return Response(final_data)

    elif request.method == 'POST':
        
        # check if author even exists
        get_object_or_404(AuthorUser, uuid=uuid)

        object_type = request.data.get("type", "").lower()
        if object_type not in ("post", "follow", "like", "comment"):
            return Response(status=400, data="Invalid request. Type must be one of {'post', 'follow', 'like', 'comment'}")
        
        itemType = object_type
        itemID = None

        if object_type == "post":
            
            post_cache = PostCache()

            serializer = PostsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(status=400, data=serializer.errors)
            
            data = serializer.validated_data

            post_data = dict(data)
            author = post_data.pop("author")
            post_data["author_uuid"] = get_id_from_url(author.get("id"))
            post_data["author_local"] = strip_slash(author.get("host")) == strip_slash(ENDPOINT)
            post_data["author_url"] = author.get("url")
            post_data["author_host"] = author.get("host")

            if not author_cache.get(post_data["author_uuid"]):
                ForeignAuthor.objects.update_or_create(uuid=post_data["author_uuid"], author_json=author)
                author_cache.add(post_data["author_uuid"], author)

            post_data["uuid"] = get_part_from_url(post_data["id"], "posts")
            print("UUID:", get_part_from_url(post_data["id"], "posts"))

            for extra in ("type","id"):
                post_data.pop(extra)

            # update visibility only if new and remote or local and private
            if post_data["visibility"] != "PUBLIC":
                # shared with current author
                shared_author = AuthorUser.objects.get(uuid=uuid)
                ad = AuthorDetail(shared_author.uuid, shared_author.url, shared_author.host)
                author_obj = ad.formMapping()

                try: post = Posts.objects.get(uuid=post_data["uuid"])
                except: post = None
                if post and author_obj not in post.sharedWith:
                    post_data["sharedWith"] = post.sharedWith + [author_obj]
                else:
                    post_data["sharedWith"] = [author_obj]
            
            itemID = post_data["uuid"]

            try: post = Posts.objects.get(uuid=itemID)
            except: post = Posts(uuid=itemID)

            post_cache.add(post_data["uuid"], dict(serializer.validated_data))
                           
            if post:
                post_data.pop("uuid")

            for key, value in post_data.items():
                setattr(post, key, value)
            post.save()
            
        
        elif object_type == "follow":
            serializer = FollowRequestsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(status=400, data=serializer.errors)
            
            data = serializer.validated_data
            summary = data["summary"]
            requester_uuid = get_id_from_url(data["actor"]["id"])
            requester_host = data["actor"]["host"]
            requester_url = data["actor"]["url"]

            if not author_cache.get(requester_uuid):
                ForeignAuthor.objects.update_or_create(uuid=requester_uuid, author_json=data["actor"])
                author_cache.add(requester_uuid, data["actor"])

            if not sender:
                ad = AuthorDetail(requester_uuid, requester_url, requester_host)
                sender = ad.formMapping()

            FollowRequests.objects.update_or_create(summary=summary, recipient_uuid=uuid, requester_uuid=requester_uuid, requester_host=requester_host, requester_url=requester_url)

            frq = FollowRequests.objects.get(recipient_uuid=uuid, requester_uuid=requester_uuid)
            itemID = frq.id
        
        elif object_type == "like":
            serializer = LikeSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(status=400, data=serializer.errors)
            
            data = serializer.validated_data
            liked_id = get_id_from_url(data["object"])
            author_uuid = get_id_from_url(data["author"]["id"])
            author_host = data["author"]["host"]
            author_url = data["author"]["url"]

            if not author_cache.get(author_uuid):
                ForeignAuthor.objects.update_or_create(uuid=author_uuid, author_json=data["author"])
                author_cache.add(author_uuid, data["author"])

            if not sender:
                ad = AuthorDetail(author_uuid, author_url, author_host)
                sender = ad.formMapping()

            obj_type = get_object_type(data["object"])

            if obj_type == "post":
                post = get_object_or_404(Posts, uuid=liked_id)
                likeCount = post.likeCount
                post.likeCount = likeCount + 1
                post.save()

            Likes.objects.update_or_create(context = data["context"], liked_id=liked_id, summary = data["summary"], author_uuid=author_uuid, author_host=author_host, author_url=author_url, liked_object_type=obj_type, liked_object=data["object"])

            like = Likes.objects.get(author_uuid=author_uuid, liked_object=data["object"])
            itemID = like.id

        elif object_type == "comment":
            serializer = CommentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(status=400, data=serializer.errors)
            
            data = serializer.validated_data
            author_uuid = get_id_from_url(data["author"]["id"])
            author_host = data["author"]["host"]
            author_url = data["author"]["url"]

            if not author_cache.get(author_uuid):
                ForeignAuthor.objects.update_or_create(uuid=author_uuid, author_json=data["author"])
                author_cache.add(author_uuid, data["author"])

            if not sender:
                ad = AuthorDetail(author_uuid, author_url, author_host)
                sender = ad.formMapping()

            comment_url = data["id"]
            comment_uuid = get_part_from_url(comment_url, "comments")

            post_id = get_part_from_url(comment_url, "posts")
            post = get_object_or_404(Posts, uuid=post_id)

            comment_count = post.count
            post.count = comment_count + 1
            post.save()

            Comments.objects.update_or_create(comment=data["comment"], contentType=data["contentType"], uuid=comment_uuid, post=post, author_uuid=author_uuid, author_host=author_host, author_url=author_url)

            itemID = comment_uuid

        
        item = InboxItem(itemType, itemID, sender)
        found = -1
        for i in range(len(inbox.items)):
            if item.checkSame(inbox.items[i]):
                found = i
        
        if found != -1:
            del inbox.items[found]
        
        inbox.items.append(item.formMapping())
        inbox.save()

        # respond with 200 and the inbox item json
        return Response(status=200, data=serializer.validated_data)

    elif request.method == 'DELETE':
        if request.user.id != author.id:
            return Response(status=401)
    
        inbox.items.clear()
        inbox.save()
        return Response(status=204)