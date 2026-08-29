// scripts/verify_sh3d.java — lê um .sh3d com o parser do próprio Sweet Home 3D, sem GUI.
//
// Prova que o zip gerado por `arch-engine pack-sh3d` (só `Home.xml`, sem a entrada
// serializada `Home`) é aceito e que o `model="modelo/modelo.obj"` resolve dentro do zip.
//
// Uso (Java 11+ executa fonte direto):
//   SH3D_JAR_DIR=/usr/share/sweethome3d java -cp "$SH3D_JAR_DIR/sweethome3d.jar:/usr/share/java/j3dcore.jar:/usr/share/java/j3dutils.jar" \
//        scripts/verify_sh3d.java examples/eco-house-demo/cad/render/modelo.sh3d
//   (ou `scripts/cli_runner.sh sh3d-check`). Jars: apt install sweethome3d libjava3d-java.
//
// Nota: `new HomeFileRecorder()` sem argumentos NÃO instala um HomeXMLHandler e falha com
// "Missing entry Home or Home.xml"; a GUI instala. Por isso usamos DefaultHomeInputStream.

import com.eteks.sweethome3d.io.ContentRecording;
import com.eteks.sweethome3d.io.DefaultHomeInputStream;
import com.eteks.sweethome3d.io.HomeXMLHandler;
import com.eteks.sweethome3d.model.Home;
import com.eteks.sweethome3d.model.HomeLight;
import com.eteks.sweethome3d.model.HomePieceOfFurniture;
import com.eteks.sweethome3d.model.Room;
import java.io.File;
import java.io.InputStream;

public class verify_sh3d {
  public static void main(String[] args) throws Exception {
    if (args.length != 1) {
      System.err.println("uso: verify_sh3d <arquivo.sh3d>");
      System.exit(64);
    }
    Home home;
    try (DefaultHomeInputStream in = new DefaultHomeInputStream(
        new File(args[0]), ContentRecording.INCLUDE_ALL_CONTENT, new HomeXMLHandler(), null, false)) {
      home = in.readHome();
    }
    System.out.println("home: " + home.getName() + " · pé-direito " + home.getWallHeight() + " cm · versão " + home.getVersion());
    for (HomePieceOfFurniture p : home.getFurniture()) {
      String tipo = p instanceof HomeLight ? "luz  " : "peça ";
      System.out.println("  " + tipo + p.getName() + " · " + p.getWidth() + " × " + p.getDepth() + " × " + p.getHeight()
          + " cm em (" + p.getX() + ", " + p.getY() + ")");
      try (InputStream model = p.getModel().openStream()) {
        byte[] head = model.readNBytes(32);
        System.out.println("         modelo lido do zip: \"" + new String(head, "UTF-8").split("\n")[0] + "\"");
      }
    }
    for (Room r : home.getRooms()) {
      System.out.println("  cômodo " + r.getName() + " · " + (r.getArea() / 10000) + " m²");
    }
    if (home.getCompass() != null) {
      System.out.println("  bússola norte=" + home.getCompass().getNorthDirection() + " rad");
    }
    System.out.println("ok: Home.xml aceito pelo Sweet Home 3D");
  }
}
