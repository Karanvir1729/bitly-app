public class MultiThreading{
    public static void main(String[] args){
        for(int i =0; i<=3; i++){
            MultithreadThing myThing = new MultithreadThing(i);
            Thread thread = new Thread(myThing);
            thread.start();
        }
    }
}