import { Flex, ScrollArea, Text } from "@radix-ui/themes";
import { useAuth } from "react-oidc-context";
import { useNavigate } from "react-router-dom";
import "./Home.css";
import Header from "../../components/Header/Header";
import UploadMain from "../../components/Upload/UploadMain";
import Footer from "../../components/Footer/Footer";
import heroImageWebp from "../../assets/hero/hero-image.webp";
import heroImageJpg from "../../assets/hero/hero-image-85-p.jpg";

const Home = () => {
  const auth = useAuth();
  const isAuthenticated = auth.isAuthenticated;
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (auth.isAuthenticated) {
      navigate("/dashboard");
    } else {
      auth.signinRedirect();
    }
  };

  return (
    <Flex
      direction="column"
      style={{
        position: "relative",
        height: "100%",
        width: "100%",
      }}
      className="pulsing-background"
    >
      <ScrollArea type="scroll">
        <Flex className="header-container">
          <div
            style={{
              maxWidth: "1312px",
              width: "100%",
            }}
          >
            {/* <a
            href="https://github.com/lumina-ai-inc/chunkr#readme"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "white", textDecoration: "none" }}
          >
            <Flex direction="row" className="temp-banner" justify="center">
              <Text className="white" size="2">
                
              </Text>
            </Flex>
          </a> */}
            <Header px="0px" home={true} />
          </div>
        </Flex>
        <div>
          <div className="hero-main-container">
            <div className="hero-image-container fade-in">
              <picture>
                <source srcSet={heroImageWebp} type="image/webp" />
                <img
                  src={heroImageJpg}
                  alt="hero"
                  className="hero-image"
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              </picture>
              <div className="hero-gradient-overlay"></div>
            </div>
            <div className="hero-content-container">
              <Flex className="hero-container">
                <Flex
                  direction="column"
                  gap="3"
                  style={{ width: "100%", height: "100%" }}
                >
                  <Flex gap="3" style={{ flex: 1 }}>
                    <Flex
                      style={{
                        flex: 1,
                        backgroundColor: "rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                      }}
                    >
                      {/* Top Left */}
                    </Flex>
                    <Flex
                      style={{
                        flex: 1,
                        backgroundColor: "rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                      }}
                    >
                      {/* Top Right */}
                    </Flex>
                  </Flex>
                  <Flex gap="3" style={{ flex: 1 }}>
                    <Flex
                      direction="column"
                      justify="end"
                      style={{
                        flex: 1,
                        backgroundColor: "rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                        paddingBottom: "48px",
                      }}
                    >
                      <Text
                        weight="medium"
                        className="scramble-text"
                        style={{
                          lineHeight: "1.2",
                          color: "white",
                          fontSize: "72px",
                        }}
                      >
                        <span
                          style={{ "--delay": "0ms" } as React.CSSProperties}
                        >
                          Open
                        </span>{" "}
                        <span
                          style={{ "--delay": "50ms" } as React.CSSProperties}
                        >
                          Source
                        </span>
                        <br />
                        <span
                          style={{ "--delay": "100ms" } as React.CSSProperties}
                        >
                          Document
                        </span>{" "}
                        <span
                          style={{ "--delay": "150ms" } as React.CSSProperties}
                        >
                          Ingestion
                        </span>
                      </Text>
                      <Flex direction="row" gap="8" mt="7">
                        <Text
                          size="4"
                          weight="bold"
                          trim="end"
                          style={{ color: "white" }}
                        >
                          Docs
                        </Text>
                        <Text
                          size="4"
                          weight="bold"
                          trim="end"
                          style={{ color: "white" }}
                        >
                          Demo
                        </Text>
                        <Text
                          size="4"
                          weight="bold"
                          trim="end"
                          style={{ color: "white" }}
                        >
                          Github
                        </Text>
                        <Text
                          size="4"
                          weight="bold"
                          trim="end"
                          style={{ color: "white" }}
                        >
                          Pricing
                        </Text>
                        <Text
                          size="4"
                          weight="bold"
                          trim="end"
                          style={{ color: "white" }}
                        >
                          Contact
                        </Text>
                      </Flex>
                    </Flex>
                    <Flex
                      style={{
                        flex: 1,
                        flexDirection: "column",
                        gap: "32px",
                        alignItems: "end",
                        justifyContent: "end",
                        backgroundColor: "rgba(255, 255, 255, 0.1)",
                        borderRadius: "8px",
                        paddingBottom: "48px",
                      }}
                    >
                      <Flex
                        direction="column"
                        gap="3"
                        px="16px"
                        py="12px"
                        style={{
                          border: "2px solid white",
                          borderRadius: "100px",
                          backgroundColor: "#FFFFFF",
                        }}
                      >
                        <Text size="4" weight="bold">
                          1500 pages in credits
                        </Text>
                      </Flex>

                      <Flex
                        direction="column"
                        gap="3"
                        p="24px"
                        style={{
                          border: "2px solid white",
                          borderRadius: "8px",
                        }}
                      >
                        <Text size="6" weight="bold" style={{ color: "white" }}>
                          Get started for free
                        </Text>
                      </Flex>
                    </Flex>
                  </Flex>
                </Flex>
              </Flex>
            </div>
          </div>
        </div>

        <Footer />
      </ScrollArea>
    </Flex>
  );
};

export default Home;

// curl -X POST https://api.chunkmydocs.com/api/task \ <br></br>
// -H "Content-Type: application/json" \ <br></br>
// -H "Authorization:{"{your_api_key}"}" \ <br></br>
// -F "file=@/path/to/your/file.pdf" \ <br></br>
// -F "model=Fast" \ <br></br>
// -F "target_chunk_length=512"
