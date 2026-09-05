from products_app.models import Review,Category, ProductList,SeasonChange,Order
from products_app.api.serializers import ReviewSerializer,CategorySerializer,ProductListSerializer,SeasonChangeSerializer,OrderCreateSerializer,OrderSerializer,ContactMessageSerializer
from products_app.services.contact_emails import send_contact_notification
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics,mixins,viewsets, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS, BasePermission
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
# from watchlist_app.api.permissions import AdminOrReadOnly,ReviewUserOrReadOnly


class IsAdminOrReadOnly(BasePermission):
    """Public read (GET/HEAD/OPTIONS); writes require a staff user."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

from django.db import transaction
from products_app.services.email_receipts import send_order_receipt



class SeasonChangeAV(APIView):
  def get(self, request):
    season=SeasonChange.objects.filter(active=True).first()
    if not season:
            return Response({}, status=status.HTTP_204_NO_CONTENT)
    serializer=SeasonChangeSerializer(season)
    return Response(serializer.data)


class UserReview(generics.ListAPIView):
  serializer_class=ReviewSerializer
  
  def get_queryset(self):
    username=self.request.query_params.get('username',None)
    return Review.objects.filter(review_user__username=username)
    # return super().get_queryset()

class ReviewCreate(generics.CreateAPIView):
  permission_classes = [IsAuthenticated]
  serializer_class=ReviewSerializer
  queryset = Review.objects.all()
  
  def perform_create(self, serializer):
    pk=self.kwargs.get('pk')
    product=ProductList.objects.get(pk=pk)
    
    review_user=self.request.user
    review_queryset=Review.objects.filter(productlist=product, review_user=review_user)
    
    if review_queryset.exists():
      raise ValidationError("You have already reviewed this movie")
    
    if product.number_rating==0:
      product.avg_rating=serializer.validated_data['rating']
    else:
      product.avg_rating=(product.avg_rating*product.number_rating+serializer.validated_data['rating'])/(product.number_rating+1)
    
    product.number_rating=product.number_rating+1
    product.save()
    serializer.save(productlist=product, review_user=review_user)


class ReviewList(generics.ListAPIView):
  # queryset=Review.objects.all()
  permission_classes = [IsAuthenticated]
  serializer_class=ReviewSerializer
  
  def get_queryset(self):
    pk=self.kwargs['pk']
    return Review.objects.filter(watchlist=pk)
  
class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
  queryset=Review.objects.all()
  serializer_class=ReviewSerializer
  # permission_classes = [ReviewUserOrReadOnly]
  
  
class ProductFilter(filters.FilterSet):
    # e.g. ?category=Keychains
    category = filters.CharFilter(field_name="category__name", lookup_expr="iexact")
    # e.g. ?color=Red   (or ?colour=Red if you prefer British spelling)
    color = filters.CharFilter(field_name="color_options__colour__name", lookup_expr="iexact")
    # keep direct fields on ProductList here:
    on_sale = filters.BooleanFilter()
    active = filters.BooleanFilter()
    wishlist = filters.BooleanFilter()
    best_selling = filters.BooleanFilter()
    title = filters.CharFilter(lookup_expr="icontains")
    id = filters.NumberFilter()

    class Meta:
        model = ProductList
        fields = ["title", "category", "color", "on_sale", "active", "wishlist", "best_selling", "id"]
  
class ProductListFilter(generics.ListAPIView):
  queryset = ProductList.objects.all()
  serializer_class=ProductListSerializer
  filter_backends = [DjangoFilterBackend]  
  # filterset_fields = ['title', 'category__name','colour','on_sale','active','wishlist','best_selling','id']
  filterset_class=ProductFilter
  
  
  
@api_view(['GET','POST'])
@permission_classes([IsAdminOrReadOnly])
def product_list(request):
  if request.method=='GET':
    products=ProductList.objects.all()
    serializer=ProductListSerializer(products,many=True)
    return Response(serializer.data)
  
  if request.method=='POST':
    serializer=ProductListSerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data)
    else:
      return Response(serializer.errors)


@api_view(['GET','PUT','DELETE'])
@permission_classes([IsAdminOrReadOnly])
def product_details(request,id):
  if request.method=='GET':
    movie=ProductList.objects.get(pk=id)
    serializer=ProductListSerializer(movie)
    return Response(serializer.data)
  
  if request.method=='PUT':
    movie=ProductList.objects.get(pk=id)
    serializer=ProductListSerializer(movie,data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data)
    else:
      return Response(serializer.errors)
    
  if request.method=="DELETE":
    movie=ProductList.objects.get(pk=id)
    movie.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
  
  
class CategoryFilter(generics.ListAPIView):
  queryset = Category.objects.all()
  serializer_class=CategorySerializer
  filter_backends = [DjangoFilterBackend]  
  filterset_fields = ['name','about','image','active',]
  
class CategoryAV(APIView):
  permission_classes = [IsAdminOrReadOnly]
  def get(self, request):
    category=Category.objects.all()
    serializer=CategorySerializer(category, many=True)
    return Response(serializer.data)
  
  
  def post(self,request):
    serializer=CategorySerializer(data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data)
    else:
      return Response(serializer.errors)
    
    
class CategoryDetailAV(APIView):
  permission_classes = [IsAdminOrReadOnly]
  def get(self, request,id):
    category=Category.objects.get(pk=id)
    serializer=CategorySerializer(category)
    return Response(serializer.data)
  
  def put(self,request,id):
    category=Category.objects.get(pk=id)
    serializer=CategorySerializer(category,data=request.data)
    if serializer.is_valid():
      serializer.save()
      return Response(serializer.data)
    else:
      return Response(serializer.errors)
  
  def delete(self,request,id):
    Category=Category.objects.get(pk=id)
    Category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
  
  
  
# class ShippingAV(APIView):
#   def get(self, request):
#     category=Category.objects.all()
#     serializer=CategorySerializer(category, many=True)
#     return Response(serializer.data)
  
  
#   def post(self,request):
#     serializer=CategorySerializer(data=request.data)
#     if serializer.is_valid():
#       serializer.save()
#       return Response(serializer.data)
#     else:
#       return Response(serializer.errors)


class OrderListCreateAV(APIView):
    """
    GET  -> list all orders (can be admin only)
    POST -> create a new order (used by checkout)
    """
    permission_classes = [permissions.AllowAny]  # restrict if needed

    def get(self, request):
        orders = Order.objects.prefetch_related("items", "items__product").order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    # def post(self, request):
    #     serializer = OrderCreateSerializer(data=request.data)
    #     if serializer.is_valid():
    #         order = serializer.save()
    #         read_serializer = OrderSerializer(order)
    #         return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.save()  # save to DB

        # --- Build the email context from the saved order ---
        # adapt the attributes below to your actual model/serializer fields
        lines = []
        for item in order.items.all():
            lines.append({
                "title": getattr(item.product, "title", str(item.product)),
                "qty": item.quantity,
                "total": float(getattr(item, "total_price", item.unit_price * item.quantity)),
            })

        order_ctx = {
            "order": {
                "number": getattr(order, "number", order.pk),
                "customer_name": getattr(order, "customer_name", ""),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
                "lines": lines,
                "subtotal": float(getattr(order, "subtotal", sum(l["total"] for l in lines))),
                "shipping": float(getattr(order, "shipping", 0)),
                "total": float(getattr(order, "total", (getattr(order, "subtotal", 0) + getattr(order, "shipping", 0)))),
            }
        }

        # choose the customer email field you store
        to_email = getattr(order, "customer_email", None) or getattr(order, "email", None)

        # --- Send the email AFTER the transaction commits (prevents duplicates) ---
        def _send():
            try:
                if to_email:
                    send_order_receipt(to_email, order_ctx)
            except Exception as e:
                # log the error; don't break the API response
                print("Email send failed:", e)

        transaction.on_commit(_send)

        read_serializer = OrderSerializer(order)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
class OrderDetailAV(APIView):
    """
    GET -> retrieve one order by ID
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            order = Order.objects.prefetch_related("items", "items__product").get(pk=pk)
        except Order.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class ContactCreateAV(APIView):
    """POST -> save a contact-form submission and notify the store owner."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        contact = serializer.save()

        # Send the notification after commit so a mail failure can't lose the message.
        def _notify():
            try:
                send_contact_notification(contact)
            except Exception as e:
                print("Contact email send failed:", e)

        transaction.on_commit(_notify)

        return Response(
            {"ok": True, "message": "Thanks! We'll get back to you shortly."},
            status=status.HTTP_201_CREATED,
        )