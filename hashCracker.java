import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.math.BigInteger;

// https://www.baeldung.com/java-md5
public class MD5BreakNumericMT implements Runnable {

    private final Work work;
    private final String hash;
    private final int length;
    private final Result result;

    public MD5BreakNumericMT(Work work, String hash, int length, Result result) {
        this.work = work;
        this.hash = hash;
        this.length = length;
        this.result = result;
    }

    @Override
    public void run() {
        breakMD5();
    }

    public static void main(String[] args) {
        String hash;
        int length;
        int numThreads;

        if (args.length >= 3) {
            // args[0] = hash, args[1] = length, args[2] = numThreads
            hash = args[0];
            length = Integer.parseInt(args[1]);
            numThreads = Integer.parseInt(args[2]);
        } else {
            // fallback to your previous hardcoded example
            hash = "ef775988943825d2871e1cfa75473ec0";
            length = 8;
            numThreads = 2;
            System.out.println("Usage: java MD5BreakNumericMT <hash> <length> <numThreads>");
            System.out.println("No or insufficient args provided, using default hash, length=8, numThreads=2.");
        }

        Work w = new Work(length);
        Result result = new Result();

        Thread[] threads = new Thread[numThreads];

        for (int i = 0; i < numThreads; i++) {
            MD5BreakNumericMT worker = new MD5BreakNumericMT(w, hash, length, result);
            threads[i] = new Thread(worker, "Worker-" + i);
            threads[i].start();
        }

        for (int i = 0; i < numThreads; i++) {
            try {
                threads[i].join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }

        if (result.password != null) {
            System.out.println("Found password: " + result.password);
        } else {
            System.out.println("Password not found");
        }
    }

    public static String toHexString(byte[] bytes) {
        StringBuilder hexString = new StringBuilder();
        for (int i = 0; i < bytes.length; i++) {
            String hex = Integer.toHexString(0xFF & bytes[i]);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        return hexString.toString();
    }

    public String breakMD5() {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            String fmt = "%0" + this.length + "d";
            int i;
            while (result.password == null && (i = this.work.getWork()) != -1) {
                String password = String.format(fmt, i);
                md.reset();
                md.update(password.getBytes());

                byte[] digest = md.digest();
                String myHash = toHexString(digest);
                if (myHash.equals(this.hash)) {
                    synchronized (result) {
                        if (result.password == null) {
                            result.password = password;
                            System.out.println("Thread " + Thread.currentThread().getName()
                                    + " found password: " + password);
                        }
                    }
                    return password;
                }
            }
            return null;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    static class Work {
        private int current = 0;
        private final int upper;

        Work(int length) {
            this.upper = (int) Math.pow(10, length);
        }

        synchronized int getWork() {
            if (this.current == -1) return -1;
            if (this.current >= this.upper) {
                this.current = -1;
                return -1;
            }
            int saved = current;
            current++;
            return saved;
        }
    }

    static class Result {
        volatile String password = null;
    }
}
