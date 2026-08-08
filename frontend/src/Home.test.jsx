import {expect,test} from "vitest";
import { render,screen } from "@testing-library/react";
import {BrowserRouter} from "react-router-dom";
import App from "./App";

//tests whether the text "URL Shortener" appears on the Home Page
test("Home page renders",()=>{
    render(
        <BrowserRouter>
            <App/>
        </BrowserRouter>
    );
    expect(screen.getByText("URL Shortener")).toBeInTheDocument();
});

