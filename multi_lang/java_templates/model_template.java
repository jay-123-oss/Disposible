// Template: JPA entity model (raw). Placeholders substituted by JavaModelGenerator.
package __PACKAGE_NAME__.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;

@Entity
public class __MODEL_NAME__ {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Long id;

  @Column(nullable = false)
  private String name;

  @Column(nullable = false)
  private Double price;

  public Long getId() {
    return id;
  }

  public String getName() {
    return name;
  }

  public Double getPrice() {
    return price;
  }
}