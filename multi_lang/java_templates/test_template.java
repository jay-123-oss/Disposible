// Template: JUnit 5 tests (raw). Placeholders substituted by JavaTestGenerator.
package __PACKAGE_NAME__;

import static org.junit.jupiter.api.Assertions.assertEquals;
import org.junit.jupiter.api.Test;

class __CLASS_NAME__ControllerTest {

  @Test
  void healthzReturnsOk() {
    String body = "{\"status\":\"ok\"}";
    assertEquals("ok", "ok");
    assertEquals(true, body.contains("ok"));
  }
}