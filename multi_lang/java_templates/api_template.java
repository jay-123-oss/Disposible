// Template: Spring Boot REST controller (raw). Placeholders substituted by JavaApiGenerator.
package __PACKAGE_NAME__;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class __CLASS_NAME__Controller {

  @GetMapping("/healthz")
  public String healthz() {
    return "{\"status\":\"ok\"}";
  }

  @GetMapping("/api/v1/__ROUTE__")
  public List<String> list__CLASS_NAME__() {
    return List.of();
  }
}